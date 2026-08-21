"""Multimodal fusion – text + optional image/audio understanding."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MultimodalFusion:
    """Fuse text with local/optional VLM image and optional STT audio."""

    SUPPORTED = ("text", "image", "audio")

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Adapt legacy ThinkingBrain inputs to the canonical fusion result.

        The core brain still calls a perception ``process`` method.  This
        adapter preserves that contract while delegating all actual work to
        ``fuse`` so text-only operation remains dependency-light.
        """
        if isinstance(input_data, dict):
            result = self.fuse(
                text=input_data.get("text") or input_data.get("query"),
                image=input_data.get("image"),
                audio=input_data.get("audio"),
            )
        elif isinstance(input_data, (list, tuple)):
            result = self.fuse(text=" ".join(str(item) for item in input_data))
        else:
            result = self.fuse(text=str(input_data or ""))

        modalities = result.get("modalities") or ["text"]
        result["summary"] = result.get("fused_text") or ""
        result["modality"] = modalities[0]
        result["confidence"] = 0.9 if result.get("ok") else 0.3
        return result

    def fuse(
        self,
        text: Optional[str] = None,
        image: Any = None,
        audio: Any = None,
        *,
        use_vlm: bool = True,
        use_stt: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        parts: List[str] = []
        modalities: List[str] = []
        details: Dict[str, Any] = {}
        ok = True
        errors: List[str] = []

        if text:
            modalities.append("text")
            parts.append(str(text).strip())

        image_path = image if isinstance(image, str) else None
        if image_path:
            modalities.append("image")
            try:
                from multimodal.understand import understand_image

                img = understand_image(image_path, use_vlm=use_vlm, inject_facts=False)
                details["image"] = {
                    "ok": img.get("ok"),
                    "summary": img.get("summary"),
                    "palette": (img.get("local") or {}).get("palette_names"),
                    "vlm_ok": bool((img.get("vlm") or {}).get("ok")),
                }
                if img.get("summary"):
                    parts.append(f"[image] {img['summary'][:500]}")
                elif not img.get("ok"):
                    errors.append(str(img.get("error") or "image understand failed"))
                    ok = False
            except Exception as e:
                details["image"] = {"ok": False, "error": str(e)}
                errors.append(str(e))
                ok = False

        audio_path = audio if isinstance(audio, str) else None
        if audio_path:
            modalities.append("audio")
            try:
                from multimodal.audio import understand_speech, audio_info

                info = audio_info(audio_path)
                details["audio_info"] = info
                if use_stt:
                    stt = understand_speech(audio_path)
                    details["audio"] = {
                        "ok": stt.get("ok"),
                        "backend": stt.get("backend"),
                        "transcript": stt.get("transcript"),
                    }
                    if stt.get("transcript"):
                        parts.append(f"[speech] {str(stt['transcript'])[:500]}")
                    elif not stt.get("ok"):
                        # meta-only is soft fail, not hard error
                        details["audio"]["note"] = stt.get("error") or "no STT backend"
                else:
                    details["audio"] = {"ok": True, "meta_only": True, "info": info}
            except Exception as e:
                details["audio"] = {"ok": False, "error": str(e)}
                errors.append(str(e))

        fused = "\n".join(p for p in parts if p).strip()
        return {
            "ok": ok if modalities else False,
            "fused_text": fused or (text or ""),
            "modalities": modalities or (["text"] if text else []),
            "details": details,
            "errors": errors,
            "experimental": "image" in modalities or "audio" in modalities,
        }

    def status(self) -> Dict[str, Any]:
        image_ok = False
        audio_ok = False
        try:
            from multimodal.vision import vision_available

            image_ok = bool(vision_available().get("ok") or vision_available().get("pillow"))
        except Exception:
            try:
                from multimodal.image_ops import list_supported

                image_ok = bool(list_supported())
            except Exception:
                pass
        try:
            from multimodal.audio import audio_available

            audio_ok = bool(audio_available().get("ok"))
        except Exception:
            pass
        return {
            "supported": list(self.SUPPORTED),
            "image": image_ok,
            "audio": audio_ok,
            "note": "Fusion uses local image analysis + optional VLM/STT backends",
        }


multimodal_fusion = MultimodalFusion()
