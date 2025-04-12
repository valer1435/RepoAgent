# RepoAgent+

This is a fork with some enhancements of RepoAgent, thanks to them for nice job.
Please refer to [Original repo](https://github.com/OpenBMB/RepoAgent) for additional information.

With this project you can generate good looking documentation for your python project just in one click!

## ✨ New features, comparing with original project

- **📝 Multi-step generation approach provides more precise results.**
- **🔍 Generation both of python files and module summaries**
- **📚 Docstring generation instead fixed markdown pages.**
- **🤖 Integration with mkdocs makes documentation more flexible for changes**



## 🚀 Getting Started

### Installation Method

#### Using pip (Recommended for Users)

Install the `repoagent` package directly using pip using this source repo:

```bash
pip install repoagent@git+https://github.com/valer1435/RepoAgent
```

### Configuring RepoAgent

Before configuring specific parameters for RepoAgent, please ensure that the OpenAI API is configured as an environment variable in the command line:

```sh
export OPENAI_API_KEY=YOUR_API_KEY # on Linux/Mac
set OPENAI_API_KEY=YOUR_API_KEY # on Windows
$Env:OPENAI_API_KEY = "YOUR_API_KEY" # on Windows (PowerShell)
```

## Run RepoAgent

Enter the root directory of RepoAgent and try the following command in the terminal:
```sh
repoagent run #this command will generate doc, or update docs(pre-commit-hook will automatically call this)
repoagent run --print-hierarchy # Print how repo-agent parse the target repo
```

The run command supports the following optional flags (if set, will override config defaults):

- `-m`, `--model` TEXT: Specifies the model to use for completion. Default: `gpt-3.5-turbo`
- `-t`, `--temperature` FLOAT: Sets the generation temperature for the model. Lower values make the model more deterministic. Default: `0.2`
- `-r`, `--request-timeout` INTEGER: Defines the timeout in seconds for the API request. Default: `60`
- `-b`, `--base-url` TEXT: The base URL for the API calls. Default: `https://api.openai.com/v1`
- `-tp`, `--target-repo-path` PATH: The file system path to the target repository. Used as the root for documentation generation. Default: `path/to/your/target/repository`
- `-hp`, `--hierarchy-path` TEXT: The name or path for the project hierarchy file, used to organize documentation structure. Default: `.project_doc_record`
- `-mdp`, `--markdown-docs-path` TEXT: The folder path where Markdown documentation will be stored or generated. Default: `markdown_docs`
- `-i`, `--ignore-list` TEXT: A list of files or directories to ignore during documentation generation, separated by commas.
- `-l`, `--language` TEXT: The ISO 639 code or language name for the documentation. Default: `Chinese`
- `-ll`, `--log-level` [DEBUG|INFO|WARNING|ERROR|CRITICAL]: Sets the logging level for the application. Default: `INFO`

You can also try the following feature

```sh
repoagent clean # Remove repoagent-related cache
repoagent diff # Check what docs will be updated/generated based on current code change
```

If it's your first time generating documentation for the target repository, RepoAgent will automatically create a JSON file maintaining the global structure information and a folder named Markdown_Docs in the root directory of the target repository for storing documents.

Once you have initially generated the global documentation for the target repository, or if the project you cloned already contains global documentation information, you can then seamlessly and automatically maintain internal project documentation with your team by configuring the **pre-commit hook** in the target repository! 

You also can use mkdocs `mkdocs gh-deploy` command to automatically deploy documentation on gh-pages. For example docuemtation for this repo is fully AI-generated by RepoAgent+ https://valer1435.github.io/RepoAgent/
### Note

Project is in developing stage, so some features may just not work :) If you see any problem - please make an issue.
