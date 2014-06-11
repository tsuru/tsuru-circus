import os


def load_envs(path):
    envs = {}
    if os.path.exists(path):
        with open(path) as file:
            for line in file.readlines():
                if "export" in line:
                    line = line.replace("export ", "")
                    k, v = line.split("=", 1)
                    v = v.replace("\n", "").replace('"', '')
                    envs[k] = v
    return envs
