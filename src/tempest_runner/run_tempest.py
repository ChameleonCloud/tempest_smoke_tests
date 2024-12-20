import argparse
import logging
import os
import tempfile

from tempest.cmd.init import TempestInit
from tempest.cmd.run import TempestRun
from tempest.cmd.workspace import WorkspaceManager

logging.basicConfig()
LOG = logging.getLogger(__name__)


class TestArgs(object):
    config_file = None

    workspace: str
    workspace_path: str
    concurrency: int
    smoke: bool
    list_tests: bool
    parallel: bool = True
    subunit: bool = False

    regex: str

    exclude_list: str

    worker_file = None
    state = None
    black_regex = None
    exclude_regex = None
    blacklist_file = None
    whitelist_file = None
    include_list = None

    def __getattr__(self, name):
        return None


class TempestManager:
    def __init__(
        self, base_path: str, config_base_path: str, test_config_dir: str
    ) -> None:
        self.base_path = base_path
        self.workspaces_yaml_path = os.path.join(self.base_path, "workspaces.yaml")
        self.config_base_path = config_base_path

        self.test_lists_base = test_config_dir

        self.workspace_manager = WorkspaceManager(self.workspaces_yaml_path)
        self.workspace_initializer = TempestInit(app=None, app_args=None, cmd_name=None)
        self.test_runner = TempestRun(app=None, app_args=None, cmd_name=None)

    def _update_accts_yaml(self, local_dir):
        etc_dir = os.path.join(local_dir, "etc")
        config_path = os.path.join(etc_dir, "tempest.conf")
        accounts_yaml = os.path.join(etc_dir, "accounts.yaml")

        config_parse = self.workspace_initializer.get_configparser(config_path)

        # Set test_accounts_file in tempest conf
        config_parse.set("auth", "test_accounts_file", accounts_yaml)

        # write out a new file with the updated configurations
        with open(config_path, "w+") as conf_file:
            config_parse.write(conf_file)

    def register_workspace(self, workspace_name):
        workspace_destination = os.path.join(self.base_path, workspace_name)
        source_config_dir = os.path.join(self.config_base_path, workspace_name)

        os.mkdir(workspace_destination)
        self.workspace_initializer.create_working_dir(
            workspace_destination, source_config_dir
        )
        self._update_accts_yaml(workspace_destination)
        self.workspace_manager.register_new_workspace(
            workspace_name, workspace_destination
        )

    def run_tests(self, workspace_name, **kwargs):
        """Run tempest command in workspace"""

        # ta = TestArgs()

        ta = argparse.Namespace(
            workspace=workspace_name,
            workspace_path=self.workspaces_yaml_path,
            exclude_list=os.path.join(self.test_lists_base, "exclude_list"),
            config_file=None,
            state=None,
            black_regex=None,
            exclude_regex=None,
            blacklist_file=None,
            whitelist_file=None,
            include_list=None,
            parallel=True,
            subunit=False,
            worker_file=None,
            load_list=None,
            combine=None,
            **kwargs,
        )

        # ta.workspace_path = self.workspaces_yaml_path
        # ta.workspace = workspace_name

        # ta.upda
        # ta.exclude_list = os.path.join(self.test_lists_base, "exclude_list")

        # LOG.info("invoking tempest with args %s", ta.__dict__)
        self.test_runner.take_action(ta)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--site", type=str)
    parser.add_argument("--list_tests", action="store_true")

    parser.add_argument("--concurrency", type=int, default=1)

    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument("--smoke", action="store_true")
    target_group.add_argument("--regex", type=str)

    parsed_args = parser.parse_args()
    return parsed_args


def main():
    parsed_args = parse_args()

    args_dict = vars(parsed_args)

    site = args_dict.pop("site")
    if not site:
        exit(1)

    ### Initialize config dirs from base config files
    with tempfile.TemporaryDirectory() as scratch_dir_name:
        our_parent_dir = os.path.dirname(os.path.abspath(__file__))
        source_config_dir_base = os.path.join(our_parent_dir, "reference_configs")
        test_config_lists = os.path.join(our_parent_dir, "test_sets")

        tempest_mgr = TempestManager(
            base_path=scratch_dir_name,
            config_base_path=source_config_dir_base,
            test_config_dir=test_config_lists,
        )

        tempest_mgr.register_workspace(site)
        tempest_mgr.run_tests(site, **args_dict)


if __name__ == "__main__":
    main()
