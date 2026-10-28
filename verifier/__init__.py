from contract import Task, Tool

from . import lsh

TOOLS = {
    Tool.MATCH_BANDS: lsh,
}

TASKS = {
    Task.FIND_LSH_CANDIDATES: lsh.verify_task,
}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task, arguments, output, reference, workspace):
    return TASKS[Task(task)](arguments, output, reference, workspace)
