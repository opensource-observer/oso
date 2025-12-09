import base64
import os
import re
import subprocess
import sys
import termios
import textwrap
import time
from io import StringIO
from typing import Any, Callable, Dict, Optional, TextIO, Union

import googleapiclient.discovery  # type: ignore
from boltons import fileutils
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery, service_usage
from google.cloud.bigquery import Dataset, DatasetReference
from google.cloud.resourcemanager import GetProjectRequest, Project, ProjectsClient
from google.cloud.service_usage import EnableServiceRequest
from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from rich import print
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.prompt import Confirm, InvalidResponse, Prompt, PromptBase
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from ruamel.yaml import YAML

LOGO = """
                  .*#%&&&#/,            
            ,%@@@@@@@@@@@@@@@@@@@*      
        .&@@@@@&,.           .(@@.      
      (@@@@(       ,*/((/*,.            
    (@@@@     *@@@@@@@@@@@@@@@,         
   @@@@.   ,@@@@@,          *.          
  @@@&    @@@@,    ,/%@@#/.(@@@@*       
 @@@&   .@@@&    &@@@@@@@@   .@@@@&     
(@@@*   @@@%   ,@@@&    *@%.    %@@@#   
%@@@.   @@@(   *@@@     #@@@@/    @@@@. 
(@@@*   @@@#    @@@@*     .@@@@.   #@@@ 
 @@@&   .@@@%    ,@@@@@*    (@@@.   @@@&
 .@@@%    @@@@,     .@@@&    &@@@   *@@@
   @@@&    ,@@@@@.   .@@@,   &@@@   ,@@@
    %@@@%     /@    .@@@&   .@@@#   (@@@
      #@@@@/  *@@@@@@@@/    @@@%   ,@@@%
        .@@@@. .,//,.     %@@@(    @@@% 
           ./.        *%@@@@#    /@@@%  
          /@@@@@@@@@@@@@@(     /@@@@.   
               ......       *@@@@@.     
       /@@&/,         .*#@@@@@@*        
       .(@@@@@@@@@@@@@@@@@@,          
"""


NEW_PROJECT_OPTION_KEY = "zzzzzz__new__"


def create_service_account(project_id: str, name: str, display_name: str) -> dict:
    """Creates a service account."""

    credentials = Credentials.from_authorized_user_file(
        filename=os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        ),
    )

    service = googleapiclient.discovery.build("iam", "v1", credentials=credentials)

    my_service_account = (
        service.projects()
        .serviceAccounts()
        .create(
            name="projects/" + project_id,
            body={"accountId": name, "serviceAccount": {"displayName": display_name}},
        )
        .execute()
    )

    print("Created service account: " + my_service_account["email"])
    return my_service_account


def get_service_account(project_id: str, name: str, display_name: str) -> dict:
    """Gets a service account."""

    credentials = Credentials.from_authorized_user_file(
        filename=os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        ),
    )

    service = googleapiclient.discovery.build("iam", "v1", credentials=credentials)

    my_service_account = (
        service.projects()
        .serviceAccounts()
        .get(
            name=f"projects/{project_id}/serviceAccounts/{name}@{project_id}.iam.gserviceaccount.com"
        )
        .execute()
    )
    return my_service_account


def create_key(service_account_email: str, write_path: str) -> None:
    """Creates a key for a service account."""

    credentials = Credentials.from_authorized_user_file(
        filename=os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        ),
    )

    service = googleapiclient.discovery.build("iam", "v1", credentials=credentials)

    key = (
        service.projects()
        .serviceAccounts()
        .keys()
        .create(
            name=f"projects/-/serviceAccounts/{service_account_email}",
            body={},
        )
        .execute()
    )

    # The privateKeyData field contains the base64-encoded service account key
    # in JSON format.
    # TODO(Developer): Save the below key {json_key_file} to a secure location.
    #  You cannot download it again later.
    json_key_file = base64.b64decode(key["privateKeyData"]).decode("utf-8")

    with open(write_path, "w") as f:
        f.write(json_key_file)


def delete_key(service_account_email: str, key_id: str) -> None:
    """Deletes a service account key."""

    name = f"projects/-/serviceAccounts/{service_account_email}/keys/{key_id}"

    credentials = Credentials.from_authorized_user_file(
        filename=os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        ),
    )

    service = googleapiclient.discovery.build("iam", "v1", credentials=credentials)

    service.projects().serviceAccounts().keys().delete(name=name).execute()


def get_iam_policy(client: ProjectsClient, project_id: str):
    # Create a client

    # Initialize request argument(s)
    request = iam_policy_pb2.GetIamPolicyRequest(
        resource=f"projects/{project_id}",
    )

    # Make the request
    resp = client.get_iam_policy(request=request)
    return resp


def set_iam_policy(client: ProjectsClient, project_id: str, new_policy: dict):
    request = iam_policy_pb2.SetIamPolicyRequest(
        resource=f"projects/{project_id}", policy=new_policy
    )

    return client.set_iam_policy(request=request)


def iam_policy_add_member(
    client: ProjectsClient, project_id: str, role: str, member: str
):
    policy = get_iam_policy(client, project_id)
    policy = modify_policy_add_role(policy, role, member)
    return set_iam_policy(client, project_id, policy)


def modify_policy_add_role(policy: dict, role: str, member: str) -> dict:
    """Adds a new role binding to a policy."""

    updated = False
    print(policy.bindings)
    for binding in policy.bindings:
        print(binding)
        if binding.role == role:
            updated = True
            if member in binding.members:
                return policy
    if not updated:
        binding = policy_pb2.Binding()
        binding.role = role
        binding.members.append(member)
        policy.bindings.append(binding)
    return policy


def wait_key():
    """Wait for a key press on the console and return it."""
    result = None
    if os.name == "nt":
        import msvcrt

        result = msvcrt.getwch()
    else:
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result


def full_wait_key():
    r = wait_key()
    for i in range(2):
        if i == 0 and ord(r) != 27:
            return r
        else:
            r += wait_key()
    return r


class MultipleChoiceInput:
    def __init__(self, choices: Dict[str, str]):
        self.choices = choices
        self.choices_list = sorted(list(self.choices.keys()))

    def render(self) -> str:
        def render_table(selected: str) -> Table:
            table = Table(show_header=False)
            table.add_column("choice")
            for choice_key in self.choices_list:
                table.add_row(
                    self.choices[choice_key],
                    style="on green" if selected == choice_key else None,
                )
            return table

        curr = 0

        # Start with the first option selected
        table = render_table(self.choices_list[curr])
        with Live(table, auto_refresh=False) as live:
            while True:
                # Collect events until released
                key = full_wait_key()
                if len(key) == 1:
                    o = ord(key)
                    if o == 10:
                        return self.choices_list[curr]
                else:
                    if key == "\x1b[A":
                        curr -= 1
                    elif key == "\x1b[B":
                        curr += 1
                    else:
                        continue
                curr = curr % len(self.choices_list)
                live.update(render_table(self.choices_list[curr]))
                live.refresh()


class StringValidate(PromptBase):
    def __init__(
        self,
        prompt: Union[str, Text],
        console: Optional[Console] = None,
        validator: Callable[[str], str] = lambda a: a,
        password: bool = False,
        show_default: bool = True,
    ):
        self.validator = validator
        super().__init__(
            prompt,
            console=console,
            password=password,
            show_default=show_default,
        )

    def process_response(self, value: str) -> Any:
        v = self.validator(value)
        return super().process_response(v)

    @classmethod
    def ask(
        cls,
        prompt: Union[str, Text],
        console: Optional[Console] = None,
        validator: Callable[[str], str] = lambda a: a,
        password: bool = False,
        show_default: bool = True,
        default: Any = None,
        stream: Optional[TextIO] = None,
    ):
        return cls(
            prompt,
            console,
            validator,
            password,
            show_default,
        )(default=default, stream=stream)


VALID_PROJECT_ID_RE = re.compile("^[a-z][A-Za-z0-9-]*$")


def project_id_validator(s: str):
    if len(s) < 6:
        raise InvalidResponse("[red]GCP Project ID is too short[/red]")
    if len(s) > 30:
        raise InvalidResponse("[red]GCP Project ID is too long[/red]")
    if not VALID_PROJECT_ID_RE.match(s):
        raise InvalidResponse(
            textwrap.dedent(
                """
            [red]GCP Project ID must only contain letters, digits, and hypens
            and start with a lowercase letter[/red]
        """
            )
        )
    return s


def create_new_project() -> Project:
    print(
        textwrap.dedent(
            """
            [bold green]Let's create a new GCP Project[/bold green]
            
            You need to name the project. In general, it's fine to name it whatever
            you'd like. This name, the project ID, will appear as the first
            component of a table's reference in your bigquery datasets
            
            [yellow]Note: GCP Project IDs must be 6-30 ASCII letters, digits and
            hyphens and must start with a lower case letter.[/yellow]
            """
        )
    )
    project_id = StringValidate.ask(
        "[green]Enter a project id[/green]", None, validator=project_id_validator
    )
    p = subprocess.Popen(["gcloud", "projects", "create", project_id])
    p.wait()

    project_client = ProjectsClient()

    print("[yellow]Waiting for the API to update with the new proejct[/yellow]")
    for i in range(10):
        for project in project_client.search_projects():
            if project.project_id == project_id:
                print("")
                print(f"[green]Project {project_id} ready![/green]")
                return project
        time.sleep(10)
    print("[red]Something is wrong. Project created but couldn't be found")
    sys.exit(1)


VALID_DATASET_ID_RE = re.compile("^[A-Za-z0-9_]*$")


def dataset_name_validator(s: str):
    if len(s) > 1024:
        raise InvalidResponse("[red]Dataset ID must less than 1024[/red]")
    if not VALID_DATASET_ID_RE.match(s):
        raise InvalidResponse("Dataset must only be letters, numbers, and underscores")
    return s


def create_new_dataset(
    client: bigquery.Client, project_id: str
) -> Callable[[], Dataset]:
    def wrapped():
        print("[bold green]Let's create a new BigQuery Dataset")
        dataset_id = StringValidate.ask(
            "[green]Enter a dataset id[/green]",
            None,
            validator=dataset_name_validator,
            default="oso_playground_copy",
        )
        dataset = bigquery.Dataset(f"{project_id}.{dataset_id}")

        # For cost purposes we copy to US for now. Maybe we can give an option
        # later but this will save users a lot if they continuously egress
        dataset.location = "US"
        dataset = client.create_dataset(dataset, timeout=60)
        print("")
        print(f"[green]Dataset {dataset_id} is ready![/green]")
        return dataset.dataset_id

    return wrapped


def choose_or_create_new(
    item_name: str,
    obj_map: Dict[str, Any],
    inputs: Dict[str, str],
    create: Callable[[], Any],
) -> Any:
    if len(inputs.keys()) == 0:
        print(f"[bold red]No existing {item_name} found[/bold red]")
        print()
        return create()
    else:
        print(f"[bold green]Select a {item_name}:[/bold green]")
        input_with_create = inputs.copy()
        input_with_create[NEW_PROJECT_OPTION_KEY] = f"Create A New {item_name}..."
        id = MultipleChoiceInput(input_with_create).render()
        if id != NEW_PROJECT_OPTION_KEY:
            return obj_map[id]
        else:
            return create()


def initiate_login_to_google():
    print("[bold red]You don't seem to be logged in to Google.[/bold red]")
    print("")
    print("Attempting login through the CLI. If this fails run the following command")
    print("before trying again:")
    print("")
    print("    [green]gcloud auth application-default login[/green]")
    print("")
    p = subprocess.Popen(["gcloud", "auth", "application-default", "login"])
    p.wait()


def get_or_create_service_account(project_id: str, service_account_name: str) -> str:
    try:
        service_account = get_service_account(
            project_id, service_account_name, service_account_name
        )
        if service_account["email"]:
            return service_account["email"]
    except:
        # If we fail let's try making the service account
        service_account = create_service_account(
            project_id, service_account_name, service_account_name
        )
        if service_account["email"]:
            return service_account["email"]


def run_dbt():
    p = subprocess.Popen(["dbt", "run", "--target", "playground"])
    p.wait()


def run():
    """You're a wizard harry"""

    import warnings

    warnings.filterwarnings(
        "ignore", message="Your application has authenticated using end user"
    )

    print(Align.center(Text(LOGO)))
    print("")
    print(Align.center("""🚀🚀🚀 WELCOME TO THE OPEN SOURCE OBSERVER WIZARD 🚀🚀🚀"""))
    print("")

    projects_map: Dict[str, Project] = {}
    projects_input: Dict[str, str] = {}

    try:
        project_client = ProjectsClient()
    except DefaultCredentialsError as exc:
        if "not found" in str(exc).lower():
            initiate_login_to_google()
    project_client = ProjectsClient()

    for project in project_client.search_projects():
        projects_map[project.project_id] = project
        projects_input[project.project_id] = (
            f"{project.display_name} ({project.project_id})"
        )

    project: Project = choose_or_create_new(
        "GCP Project", projects_map, projects_input, create_new_project
    )
    if not project:
        raise Exception("No project found")

    print("")
    print(f"Searching {project.project_id} for BigQuery Datasets")

    # List bigquery datasets
    bq_client = bigquery.Client(project=project.project_id)

    datasets_map: Dict[str, Dataset] = {}
    datasets_input: Dict[str, str] = {}
    for dataset in bq_client.list_datasets(include_all=True):
        datasets_map[dataset.dataset_id] = dataset.dataset_id
        datasets_input[dataset.dataset_id] = dataset.dataset_id

    dataset_id: str = choose_or_create_new(
        "BigQuery Dataset",
        datasets_map,
        datasets_input,
        create_new_dataset(bq_client, project.project_id),
    )

    service_account_name = f"{dataset.dataset_id}-admin"
    service_account_name = service_account_name.replace("_", "-")
    service_account_email_pre = (
        f"{service_account_name}@{project.project_id}.iam.gserviceaccount.com"
    )

    print(
        f"Ensuring that dataset [yellow]{dataset_id}[/yellow] has a service account [yellow]{service_account_email_pre}[/yellow]"
    )

    ref = DatasetReference(project.project_id, dataset_id=dataset_id)
    dataset = bq_client.get_dataset(ref)

    # Enable the service account api
    print("Ensuring Service Usage APIs are enabled to allow service account creation")
    su_client = service_usage.ServiceUsageClient()
    request = EnableServiceRequest(
        name=su_client.service_path(project.project_id, "iam.googleapis.com")
    )
    operation = su_client.enable_service(request=request)

    operation.result()
    print("Service Usage API enabled")

    # Get or create a service account
    service_account_email = get_or_create_service_account(
        project.project_id, service_account_name
    )

    # Make the service account an owner of the bigquery dataset
    access_entries = list(dataset.access_entries)
    access_entries.append(
        bigquery.AccessEntry(
            role="roles/bigquery.dataEditor",
            entity_type="userByEmail",
            entity_id=service_account_email,
        ),
    )
    access_entries.append(
        bigquery.AccessEntry(
            role="roles/bigquery.user",
            entity_type="userByEmail",
            entity_id=service_account_email,
        ),
    )

    dataset.access_entries = access_entries
    dataset = bq_client.update_dataset(dataset, ["access_entries"])

    # Add the service account as a bigquery admin on the project
    # reduce the scope of this later
    iam_policy_add_member(
        project_client,
        project.project_id,
        "roles/bigquery.dataEditor",
        f"serviceAccount:{service_account_email}",
    )
    iam_policy_add_member(
        project_client,
        project.project_id,
        "roles/bigquery.user",
        f"serviceAccount:{service_account_email}",
    )

    # Download the service account key
    # First create a place to put the service account key
    oso_home_dir = os.path.expanduser("~/.config/oso/")
    fileutils.mkdir_p(oso_home_dir)
    key_file_path = os.path.join(oso_home_dir, f"{dataset.dataset_id}-keyfile.json")

    if not os.path.exists(key_file_path):
        create_key(service_account_email, key_file_path)
    else:
        # Automatically delete the key
        import json

        with open(key_file_path) as key_file:
            key = json.load(key_file)
            if key["project_id"] != project.project_id:
                print(
                    textwrap.dedent(
                        """
                    [yellow]WARNING:[/yellow]
                    An existing keyfiles does not match the current
                    project. Some GCP project may [red]lose[/red] a service account key
                    """
                    )
                )
                print("")
                if Confirm.ask("[yellow]Continue?[/yellow]"):
                    create_key(service_account_email, key_file_path)
            else:
                print("[yellow]Found existing key. Rotating[/yellow]")
                private_key_id = key["private_key_id"]
                delete_key(service_account_email, private_key_id)
                create_key(service_account_email, key_file_path)

    # Setup the configuration for the playground
    profiles_home_dir = os.path.expanduser("~/.dbt/")
    fileutils.mkdir_p(profiles_home_dir)
    profiles_path = os.path.expanduser("~/.dbt/profiles.yml")
    profiles_yml = textwrap.dedent(
        f"""
        opensource_observer:
          outputs:
            playground:
              type: bigquery
              dataset: {dataset.dataset_id} 
              job_execution_time_seconds: 300
              job_retries: 1
              location: US
              method: service-account
              keyfile: {key_file_path}
              project: {project.project_id}
              threads: 32
          target: playground
    """
    )

    yaml = YAML()
    if os.path.exists(profiles_path):
        inner = YAML()
        new_profile = inner.load(profiles_yml)

        profiles = yaml.load(open(profiles_path))

        print(
            textwrap.dedent(
                f"""
            You already have an [yellow]opensource_observer[/yellow] profile configured.
            With the following options:
            """
            )
        )

        existing = StringIO()
        yaml.dump(
            dict(opensource_observer=profiles["opensource_observer"]), stream=existing
        )
        existing.seek(0)

        updated = StringIO()
        yaml.dump(new_profile, stream=updated)
        updated.seek(0)

        config_diff = Table()
        config_diff.add_column("Existing")
        config_diff.add_column("New")
        config_diff.add_row(
            Syntax(existing.read(), "yaml"),
            Syntax(updated.read(), "yaml"),
        )
        print(config_diff)

        print("")
        if Confirm.ask("[yellow]Overwrite?[/yellow]", default=False):
            profiles["opensource_observer"] = new_profile["opensource_observer"]
            out = StringIO()
            yaml.dump(profiles, stream=out)
            out.seek(0)
            with open(profiles_path, "w") as f:
                f.write(out.read())
    else:
        print(
            textwrap.dedent(
                f"""
            [green]No dbt profile detected. Writing the following to
            [/green][bold magenta]{profiles_path}[/bold magenta]:
            """
            )
        )
        print("")
        print(Syntax(profiles_yml, "yaml"))
        with open(profiles_path, "w") as f:
            f.write(profiles_yml)

    print(
        textwrap.dedent(
            f"""
        [bold green]Everything's setup for GCP![/bold green]
        """
        )
    )
    if Confirm.ask(
        "Would you like to run [blue]dbt[/blue] to copy the latest 14 days of the [green]opensource-observer.oso[/green] BigQuery dataset?",
        default=False,
    ):
        run_dbt()

    print(
        textwrap.dedent(
            """
        [bold green]Congratulations![/bold green] You now have a new playground area setup
        and ready to go for querying or dbt development!
    """
        )
    )
