# tasks.py

class Task:
    checks = ["✅", "✔️", "☑️", "✓", "☑", "✔"]
    startId = "{#ID: "
    endId = "}"

    def parseline(self):
        stripped = self.raw.strip()
        todoremoved = stripped.replace("// TODO: ", "")

        todonextstep = todoremoved
        if Task.startId in todoremoved:
            idx1 = todoremoved.index(self.startId)
            idx2 = todoremoved.index(self.endId)
            for idx in range(idx1 + len(self.startId), idx2):
                self.todoistId += todoremoved[idx]
                todonextstep = todoremoved.replace(self.startId + self.todoistId + self.endId, "")
        else:
            self.todoistId = ""

        for check in Task.checks:
            if check in todonextstep:
                self.completed = True
                todonextstep = todonextstep.replace(check, "")

        self.title = todonextstep.split(";")[0].strip()

        try:
            desc = todonextstep.split(";")[1]
            self.description = desc.strip()
        except:
            pass

    def __init__(self, line, num, filename):
        self.section = filename
        self.lineno = num
        self.raw = line

        self.todoistId = ""
        self.title = ""
        self.description = ""
        self.completed = False
        self.parseline()

    def __str__(self):
        return self.title + " on line " + str(self.lineno) + " in " + self.parent