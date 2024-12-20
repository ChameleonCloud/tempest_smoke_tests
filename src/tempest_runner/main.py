import logging
import os
from pathlib import Path

from tempest_runner.setup_workspace import TempestManager

logging.basicConfig()
LOG = logging.getLogger(__name__)


def main():
    project_base = os.environ.get("GITHUB_WORKSPACE", ".")

    project_base_path = Path(project_base)
    workspaces_dir = project_base_path.joinpath("workspaces")
    workspaces_yaml = workspaces_dir.joinpath("workspaces.yaml")
    src_configs_dir = project_base_path.joinpath("reference_configs")

    manager = TempestManager(
        workspaces_config_path=workspaces_yaml.as_posix(),
        base_path=workspaces_dir.as_posix(),
    )

    workspaces = ["uc_dev", "uc_prod", "kvm_prod"]

    for name in workspaces:
        try:
            manager.init_and_register_workspace(
                workspace_name=name,
                workspace_src_config=src_configs_dir.joinpath(name).as_posix(),
            )
        except OSError as exc:
            # LOG.warning("workspace already exists, got error %s", exc)
            pass


if __name__ == "__main__":
    main()
