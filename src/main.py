# Import the Todoist API
from todoist_api_python.api import TodoistAPI

# Import my custom classes
from tasks.task import Task

# Import the necessary libraries
import os
import ntpath
import sys
import argparse

swiftFiles = []

def create_arg_parser():
    parser = argparse.ArgumentParser(description='A command line tool for interacting with Todoist.')
    parser.add_argument('inputDirectory', help='The root of the directory to analyze for TODO: statements.')
    parser.add_argument('projectId', help='The id of the project to update in Todoist.')
    return parser

def findSwiftFiles(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".swift"):
                # print(os.path.join(root, file))
                swiftFiles.append(os.path.join(root, file))
    
    return swiftFiles

def analyzeTodoLines(files):
    todoStatements = {}
    for file in swiftFiles:
        filename = ntpath.basename(file)
        with open(file, 'r') as f:
            lines = f.readlines()
            for num, line in enumerate(lines, 1):
                if "TODO:" in line:
                    print("TODO: statement on line " + str(num) + " in " + filename)
                    task = Task(line, num, filename)

                    if filename in todoStatements.keys():
                        todoStatements[filename].append(task)
                    else:
                        todoStatements[filename] = [task]
    
    print()
    return todoStatements

def markNewlyAddedSwiftTask(swiftTask, todoistTask):
    swiftTask.todoistId = todoistTask.id

    for file in swiftFiles:
        with open(file, 'r+') as f:
            lines = f.readlines()
            for num, line in enumerate(lines, 1):
                if line == swiftTask.raw:
                    id = " {#ID: " + swiftTask.todoistId + "}"
                    strip = line.rstrip('\n')
                    newline = strip + id + '\n'
                    lines[num - 1] = newline

        with open(file, 'w') as f:
            f.write("".join(lines))

def markCompletedSwiftTask(swiftTask):
    for file in swiftFiles:
        with open(file, 'r+') as f:
            lines = f.readlines()
            for num, line in enumerate(lines, 1):
                if line == swiftTask.raw:
                    lines.remove(line)

        with open(file, 'w') as f:
            f.write("".join(lines))

def analyzeExistingTask(swiftTask, todoistTask):
    if swiftTask.todoistId == todoistTask.id:
        print("Task already exists: " + swiftTask.title)

        if swiftTask.title != todoistTask.content or swiftTask.description != todoistTask.description:
            print("Updating task: " + swiftTask.title)
            updateSuccessful = api.update_task(task_id=todoistTask.id,content=swiftTask.title, description=swiftTask.description)
            print("Update status: " + str(updateSuccessful))
        else:
            print("No updates needed.")

        print()
        if swiftTask.completed and not todoistTask.is_completed:
            print("Closing task: " + todoistTask.content)
            closeSuccessful = api.close_task(task_id=todoistTask.id)
            print("Closing status: " + str(closeSuccessful))
            print()
            markCompletedSwiftTask(swiftTask)
            return None
        else:
            return swiftTask
    else:
        pass
        # this should be an error
        # api.add_task(task.title, project_id=id, section_id=section.id)

def createNewTodoistTask(task, project_id, section_id):
    print("Creating new Todoist task in: " + task.title)
    if section_id:
        task = api.add_task(
            content=task.title, 
            description=task.description,
            project_id=project_id, 
            section_id=section_id
        )

        return task
    else:
        pass
        # this should be an error

def createNewSection(name, project_id):
    print("Creating new section: " + name)
    section = api.add_section(name=name, project_id=project_id)
    return section

def checkCompletedTasks(projectId, section):
    print(section)
    completed = api.get_completed_items(project_id=projectId, section_id=section)
    print(completed.total)
    print()
    for task in completed.items:
        print(task.content)
        print(task.id)
        print()

if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()
    print("Analyzing project directory: " + args.inputDirectory)
    print("...")

    api = TodoistAPI("09c47793536d2cd0cd44a534cea9d7d9f3240e16")

    swiftFiles = findSwiftFiles(args.inputDirectory)
    todoStatements = analyzeTodoLines(swiftFiles)

    # Update the Todoist project with the new tasks and updated tasks
    try:
        projectId = args.projectId
        project = api.get_project(project_id=projectId)
        print("Updating Todoist project: " + project.name)
        print()

        sections = api.get_sections(project_id=projectId)
        for section in sections:
            swiftTasks = todoStatements.pop(section.name, [])
            todoistTasks = api.get_tasks(project_id=projectId, section_id=section.id)

            checkCompletedTasks(projectId, section.id)
            
            for swiftTask in swiftTasks:
                todoistTask = next((task for task in todoistTasks if task.id == swiftTask.todoistId), None)
                if todoistTask:
                    updatedTask = analyzeExistingTask(swiftTask, todoistTask)
                else:
                    if swiftTask.todoistId == "":
                        newTask = createNewTodoistTask(swiftTask, projectId, section.id)
                        markNewlyAddedSwiftTask(swiftTask, newTask)
                    else:
                        markCompletedSwiftTask(swiftTask)

        for section, tasks in todoStatements.items():
            section = createNewSection(section, projectId)
            print("Creating new section: " + section.name)
            print()            
            for task in tasks:
                newTask = createNewTodoistTask(task, projectId, section.id)
                markNewlyAddedSwiftTask(task, newTask)

        sys.exit(0)
    except Exception as error:
        print(error)
        sys.exit(1)