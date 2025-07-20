# CSNETWK_Local-Social-Networking-Protocol

LSNP (Lightweight Social Networking Protocol) is a decentralized, peer-to-peer messaging system designed to operate within local area networks (LANs).

# Terminology
- Peer: A device participating in LSNP
- Profi le: User’s identity message
- Post: Public message to all peers
- DM: Private message to one peer
- Token: Expiring text credential
- Chunk: Part of a multi-packet fi le
- TTL: Time-to-live in seconds
- GameID: Identifi er for a game session
- GroupID: Identifi er for a group

# Protocol Overview
- Transport: UDP (broadcast & unicast)
- Port: 50999
- Broadcast Address: Broadcast Address of the Network
- Encoding: Plain UTF-8 text, key-value format
- Separator: KEY: VALUE
- Terminator: Blank line (\n\n) [Each message should end with a (\n\n)]

# Directory Structure

<pre>
project/
├── config.py
├── client.py
├── interface.py
├── log.py
├── router.py
├── custom_types/
│   ├── token.py
│   └── user_id.py
├── messages/
│   ├── base_message.py
│   └── ...
├── tests/
│   └── ...  
└── utils/
    └── msg_format.py

</pre>

## File/Folder Descriptions
- `client.py`: Entry point of the application; initializes sockets, threads, and config
- `config.py`: Contains code for getting the device and broadcast IPs and configuration options such as `PORT`, `ENCODING`, etc.
- `interface.py`: Serves as the view, responsible for I/O
- `log.py`: Contains helper functions for logging
- `router.py`: Responsible for dynamic importing of message types and routing incoming messages to its corresponding type
- `custom_types/`: Folder for custom data types
  - `token.py`: Custom data type implementation for the `TOKEN` field
  - `user_id.py`: Cusotm data type implementation for the `USERID` field
- `messages/`: Folder containing all message types
  - `base_message.py`: Abstract base class for all message handlers
- `utils/`: Folder for utility files
  - `msg_format.py`: Contains helper functions for formatting messages such as `serialize_message`, `deserialize_message`, etc.

# Usage

## Initialization
```
python client.py --port PORT_NUM --verbose
```

Optional arguments:
- `--port PORT_NUM`: Overrides the default port located in `config.py`
- `--verbose`: Toggles verbose mode to on

## Adding New Message Types
Each message is represented as a python file under the `messages/` folder. These are dynamically loaded by `router.py` and as such, each message type should:

- Inherit from `BaseMessage`, an abstract class defining what functionality the message should implement.
- Include `__schema__` under the implementing class, which dictates the format of the message type.
- Include `__message__` inside the module, which points to the implementing class.

Another subfolder can be used for dynamic allocation by changing `MESSAGES_DIR` in the `config.py` file.

### `__schema__`
Is a dictionary used by `validate_message` to validate the instance of the message type against. Each key value pair represents a field of the message

- `KEY`: The name of the field (usually in ALL_CAPS)
- `VALUE`: The "rules" in dictionary form.

Each RULE may include the following flags:

- `type`: The allowed data type of the field's value
- `required`: If `True` the field's values cannot be empty
- `input`: Can be set to `True`, useful to user interfaces for prompting
- `output`: Can be set to `True`, useful to user interfaces for displaying