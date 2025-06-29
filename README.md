## Question 1

## Usage

```python
from Question_1.sequential_conversation import SequentialConversationBot

bot = SequentialConversationBot()
response = bot.process_input("Is there an outlet in Petaling Jaya?")
print(response)
```

## Run Tests

```bash
cd Question_1
python test_sequential_conversation.py
```

## Demo

```bash
cd Question_1
python sequential_conversation.py
```

## Question 2

## Usage

```python
from Question_2.agentic_bot import AgenticConversationBot

bot = AgenticConversationBot()
response = bot.process_input("What is 5 + 3?")
print(response)
```

## Run Tests

```bash
cd Question_2
python -m pytest test_planner.py -v
```

## Demo

```bash
cd Question_2
python agentic_bot.py
```