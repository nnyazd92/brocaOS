from unittest.mock import Mock


def test_delete_memory_noop_when_zero_id():
    from broca.tools.memory_tool import DeleteMemoryTool

    mm = Mock()
    tool = DeleteMemoryTool(memory_manager=mm)

    res = tool.execute(memory_id=0)
    assert res["success"] is True
    assert res["memory_id"] == 0
    mm.delete_memory.assert_not_called()


def test_delete_memory_noop_when_missing_id():
    from broca.tools.memory_tool import DeleteMemoryTool

    mm = Mock()
    tool = DeleteMemoryTool(memory_manager=mm)

    res = tool.execute()
    assert res["success"] is True
    assert res["memory_id"] == 0
    mm.delete_memory.assert_not_called()


def test_delete_memory_deletes_when_valid_id():
    from broca.tools.memory_tool import DeleteMemoryTool

    mm = Mock()
    mm.delete_memory.return_value = True
    tool = DeleteMemoryTool(memory_manager=mm)

    res = tool.execute(memory_id=123)
    assert res["success"] is True
    mm.delete_memory.assert_called_once_with(123)

