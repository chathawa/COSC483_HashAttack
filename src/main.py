from pathlib import Path
from trials import *


def main():
    results_dir = Path('../results')
    if not results_dir.exists():
        results_dir.mkdir()

    trials = tuple(Trial.open_directory(Path('../results')))
    for trial in trials:
        trial.run_collision(results_dir)
        trial.run_pre_image(results_dir)


if __name__ == '__main__':
    main()
