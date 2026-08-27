"""Zenthon core exceptions."""


class ZenthonError(Exception):
    """Base exception for all Zenthon errors."""

    def __init__(self, message: str = "Zenthon error", code: str = "ZENTHON_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class KernelError(ZenthonError):
    def __init__(self, message: str = "Kernel error"):
        super().__init__(message, code="KERNEL_ERROR")


class ServiceNotFoundError(ZenthonError):
    def __init__(self, name: str):
        super().__init__(f"Service not found: {name}", code="SERVICE_NOT_FOUND")


class EventError(ZenthonError):
    def __init__(self, message: str = "Event bus error"):
        super().__init__(message, code="EVENT_ERROR")


class SchedulerError(ZenthonError):
    def __init__(self, message: str = "Scheduler error"):
        super().__init__(message, code="SCHEDULER_ERROR")


class PluginError(ZenthonError):
    def __init__(self, message: str = "Plugin error"):
        super().__init__(message, code="PLUGIN_ERROR")


class AgentError(ZenthonError):
    def __init__(self, message: str = "Agent error"):
        super().__init__(message, code="AGENT_ERROR")


class MemoryError(ZenthonError):
    def __init__(self, message: str = "Memory error"):
        super().__init__(message, code="MEMORY_ERROR")


class SecurityError(ZenthonError):
    def __init__(self, message: str = "Security violation"):
        super().__init__(message, code="SECURITY_ERROR")


class ToolContractError(ZenthonError):
    def __init__(self, message: str = "Invalid tool contract"):
        super().__init__(message, code="TOOL_CONTRACT_ERROR")


class ToolApprovalRequiredError(SecurityError):
    def __init__(self, tool_name: str):
        ZenthonError.__init__(
            self,
            f"Explicit approval is required before running tool: {tool_name}",
            code="TOOL_APPROVAL_REQUIRED",
        )
