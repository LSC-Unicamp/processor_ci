import os
import time


def wait_for_lock(lockfile, check_interval=1):
    while os.path.exists(lockfile):
        print(f"[LOCK] Aguarde... outro processo está rodando. ({lockfile})")
        time.sleep(check_interval)


def create_lock(lockfile):
    with open(lockfile, "w") as f:
        f.write(str(os.getpid()))
    print(f"[LOCK] Criado: {lockfile}")


def remove_lock(lockfile):
    if os.path.exists(lockfile):
        os.remove(lockfile)
        print(f"[LOCK] Removido: {lockfile}")
