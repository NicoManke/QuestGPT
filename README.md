# Bachelor Thesis - "Prozedurale Quest-Generierung unter Verwendung eines Large Language Models" - Repository

|  General Info  | |
| ---|---|
| Working Title | `QuestGPT` |
| Student | `Nico Manke` |
| Target Platform(s) | `Windows` |
| End Date | 27.11.2023 |
| Study Program | Games Engineering B.Sc.|
| IDE | PyCharm |
| Interpreter | Python 3.9 |
| Build System | PyInstaller |
| Python Version | 3.9.4 |

### Packages in Use
- isodate==0.6.1
- lark==1.1.7
- lxml==4.9.3
- multidict==6.0.4
- openai==0.28.0
- PyLD==2.0.3
- pymantic==1.0.0
- pyparsing==3.1.1
- pytz==2023.3.post1
- rdflib==7.0.0
- requests==2.31.0
- requests-toolbelt==1.0.0
- six==1.16.0
- tqdm==4.66.1
- urllib3==2.0.4
- yarl==1.9.2

### Abstract

`QuestGPT explores the capabilities of GPT-4 by OpenAI in terms of generating quests for a simple RPG text adventure game.`

## Repository Structure - where to find what!

```
RepositoryRoot/
    ├── README.md       
    ├── BA_PY_V1/             
    │   ├── main.py           
    │   ├── ...
    │   ├── requirements.txt
    │   └── ...
    ├── dependencies/
    │   └── Eich-Created.ttl // the file containing all RDF triplets used for filling the knowledge graph
    ├── distributable/
    │   └── QuestGPT.exe // the executable file for running the game in a simple console after installing blazegraph and starting the graph server
    └── documentation/      
        ├── Graph/  
        │   └── Installation, Setup and Usage.md // instructions and important links to follow for installing Blazegraph
        └── Python_Project/  
            └── Installation, Setup and Usage.md // instructions for setting up and using the Python project in PyCharm 
```