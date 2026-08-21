from interfaces.gui.command_center import infer_operation_mode


def test_command_center_routes_common_operations():
    assert infer_operation_mode("Python ilə təhlükəsiz API yaz") == "Code Operation"
    assert infer_operation_mode("Bu sənədi qısa xülasə et") == "Summary Operation"
    assert infer_operation_mode("Maliyyə nəticələrini analiz et") == "Analysis Operation"


def test_command_center_marks_media_and_default_reasoning():
    assert infer_operation_mode("PDF sənədini incələ") == "Multimodal Operation"
    assert infer_operation_mode("Bu məqsəd üçün plan qur") == "Reasoning Operation"
