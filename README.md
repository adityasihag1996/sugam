# sugam (सुगम)
This repository contains ollama based logic for open source AI-powered search engine.

## Table of Contents

- [Installation](#Installation)
- [Usage](#Usage)
- [To-Do](#To-Do)
- [Contributing](#contributing)

## Installation
To use this implementation, you will need to have Python >= 3.10 installed on your system, as well as the following Python libraries:

```
git clone -b dev-ollama https://github.com/adityasihag1996/sugam.git
cd sugam
pip install -r requirements.txt
```

To install ollama, follow instructions from this [repo](https://github.com/ollama/ollama).

## Usage
You can start the ollama inference server using instructions from this [repo](https://github.com/ollama/ollama).

In a standalone terminal, run ollama inference server for your model
```
ollama run llama3:8b-instruct-q8_0
```

Start the conversation bot
```
python runner.py
```

## To-Do
- [ ] Multithread google search
- [ ] Create skeleton frontend
- [ ] Smarter chat history management

## Contributing
Contributions to improve the project are welcome. Please follow these steps to contribute:

Fork the repository.\
Create a new branch for each feature or improvement.\
Submit a pull request with a comprehensive description of changes.