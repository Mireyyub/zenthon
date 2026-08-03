"""
Leon ↔ NVIDIA Omniverse bridge (Faza 8).

Omniverse (Kit / USD / Nucleus) optional dependency-dir.
Yüklü deyilsə soft-stub rejimində işləyir; reasoning + scene metadata hələ də mümkündür.

İstifadə:
    from integrations.omniverse import OmniverseBridge
    ov = OmniverseBridge()
    print(ov.status())
    print(ov.describe_scene())
    print(ov.ask_leon("Səhnədə neçə obyekt var?"))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json

from core.logger import logger


@dataclass
class SceneObject:
    path: str
    name: str
    type: str = "Xform"
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "type": self.type,
            "attributes": self.attributes,
        }


class OmniverseBridge:
    """
    Minimal bridge:
    - detect Kit / pxr (USD)
    - maintain local scene snapshot (stub və ya real)
    - publish events to Leon event_bus
    - reason over scene via ReasoningEngine
    """

    def __init__(self, stage_id: str = "default"):
        self.stage_id = stage_id
        self._objects: Dict[str, SceneObject] = {}
        self._pxr = None
        self._kit = None
        self._connected = False
        self._probe()

    def _probe(self) -> None:
        try:
            import pxr  # type: ignore

            self._pxr = pxr
            self._connected = True
            logger.info("OmniverseBridge: pxr (USD) available")
        except Exception:
            self._pxr = None
        try:
            import omni  # type: ignore

            self._kit = omni
            self._connected = True
            logger.info("OmniverseBridge: omni Kit available")
        except Exception:
            self._kit = None

        if not self._connected:
            logger.info("OmniverseBridge: offline stub mode (no Kit/USD)")

    # ---------- connection / status ----------
    def status(self) -> Dict[str, Any]:
        return {
            "bridge": "leon-omniverse",
            "stage_id": self.stage_id,
            "connected": self._connected,
            "pxr": self._pxr is not None,
            "omni_kit": self._kit is not None,
            "objects": len(self._objects),
            "mode": "live" if self._connected else "stub",
            "timestamp": datetime.now().isoformat(),
        }

    def is_available(self) -> bool:
        return bool(self._connected)

    # ---------- scene ops ----------
    def upsert_object(
        self,
        path: str,
        name: Optional[str] = None,
        obj_type: str = "Xform",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> SceneObject:
        name = name or path.rstrip("/").split("/")[-1]
        obj = SceneObject(path=path, name=name, type=obj_type, attributes=attributes or {})
        self._objects[path] = obj
        self._emit("SceneObjectUpserted", obj.to_dict())
        return obj

    def remove_object(self, path: str) -> bool:
        if path in self._objects:
            del self._objects[path]
            self._emit("SceneObjectRemoved", {"path": path})
            return True
        return False

    def list_objects(self) -> List[Dict[str, Any]]:
        return [o.to_dict() for o in self._objects.values()]

    def describe_scene(self) -> Dict[str, Any]:
        """Scene summary for Leon reasoning."""
        objs = self.list_objects()
        # Try real stage if Kit present
        live_paths: List[str] = []
        if self._kit is not None:
            try:
                import omni.usd  # type: ignore

                ctx = omni.usd.get_context()
                stage = ctx.get_stage() if ctx else None
                if stage is not None:
                    for prim in stage.Traverse():
                        live_paths.append(str(prim.GetPath()))
            except Exception as e:
                logger.debug(f"Omniverse stage traverse: {e}")

        return {
            "stage_id": self.stage_id,
            "mode": "live" if self._connected else "stub",
            "object_count": len(objs),
            "objects": objs[:50],
            "live_prim_sample": live_paths[:30],
        }

    def sync_from_stage(self) -> Dict[str, Any]:
        """Pull prims from active Omniverse stage into local snapshot."""
        if self._kit is None:
            return {"ok": False, "error": "omni Kit yoxdur – stub rejim"}
        try:
            import omni.usd  # type: ignore

            ctx = omni.usd.get_context()
            stage = ctx.get_stage() if ctx else None
            if stage is None:
                return {"ok": False, "error": "active stage yoxdur"}
            count = 0
            for prim in stage.Traverse():
                path = str(prim.GetPath())
                self.upsert_object(path, name=prim.GetName(), obj_type=prim.GetTypeName())
                count += 1
            return {"ok": True, "synced": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def load_stub_demo_scene(self) -> Dict[str, Any]:
        """Demo scene without Omniverse runtime."""
        demo = [
            ("/World", "World", "Xform"),
            ("/World/Ground", "Ground", "Mesh"),
            ("/World/Cube", "Cube", "Cube"),
            ("/World/Sphere", "Sphere", "Sphere"),
            ("/World/Light", "DomeLight", "DomeLight"),
        ]
        for path, name, t in demo:
            self.upsert_object(path, name=name, obj_type=t, attributes={"demo": True})
        return {"ok": True, "objects": len(demo)}

    # ---------- Leon cognitive ----------
    def scene_context_text(self) -> str:
        desc = self.describe_scene()
        lines = [
            f"Omniverse stage={desc['stage_id']} mode={desc['mode']}",
            f"objects={desc['object_count']}",
        ]
        for o in desc.get("objects") or []:
            lines.append(f"- {o.get('path')} ({o.get('type')})")
        return "\n".join(lines)

    def ask_leon(self, question: str, use_brain: bool = True) -> Dict[str, Any]:
        """Scene context + Leon ReasoningEngine."""
        from brain.reasoning.engine import reasoning_engine

        ctx = self.scene_context_text()
        prompt = (
            f"Sən Leon-san və NVIDIA Omniverse səhnəsi haqqında düşünürsən.\n"
            f"Səhnə:\n{ctx}\n\nSual: {question}"
        )
        result = reasoning_engine.reason(prompt, strategy="auto", use_brain=use_brain)
        result["omniverse"] = self.status()
        result["scene_object_count"] = len(self._objects)
        self._emit("LeonOmniverseQuery", {"question": question, "trace_id": result.get("trace_id")})
        return result

    def inject_scene_facts(self) -> int:
        """Scene objects → FactStore (persist)."""
        try:
            from knowledge.facts import FactStore

            fs = FactStore()
            n = 0
            for o in self._objects.values():
                fs.add(
                    f"Omniverse object {o.name} path={o.path} type={o.type}",
                    source="omniverse",
                    confidence=0.85,
                )
                n += 1
            return n
        except Exception as e:
            logger.warning(f"inject_scene_facts: {e}")
            return 0

    def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        try:
            from core.event_bus import event_bus

            event_bus.publish(event, payload, source="omniverse")
        except Exception:
            pass


def get_bridge(stage_id: str = "default") -> OmniverseBridge:
    return OmniverseBridge(stage_id=stage_id)
