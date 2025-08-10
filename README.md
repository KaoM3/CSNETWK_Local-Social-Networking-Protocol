# CSNETWK_Local-Social-Networking-Protocol

LSNP (Lightweight Social Networking Protocol) is a decentralized, peer-to-peer messaging system designed to operate within local area networks (LANs).

# Terminology
- Peer: A device participating in LSNP
- Profile: User’s identity message
- Post: Public message to all peers
- DM: Private message to one peer
- Token: Expiring text credential
- Chunk: Part of a multi-packet file
- TTL: Time-to-live in seconds
- GameID: Identifier for a game session
- GroupID: Identifier for a group

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
├── client_logger.py
├── router.py
├── custom_types/
│   ├── base_message.py
│   └── fields.py
├── messages/
│   └── ...
├── states/
│   ├── client_state.py
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
- `client_logger.py`: A globally accessible singleton containing functions for displaying information and logging to a log file
- `router.py`: Responsible for dynamic importing of message types and routing incoming messages to its corresponding type
- `custom_types/`: Folder for custom data types
  - `base_message.py`: Custom abstract base class for implementating message types
  - `fields.py`: Module containin implementation for custom data types used in message fields such as `TOKEN`, `USER_ID`, `MESSAGE_ID`, etc.
- `messages/`: Folder containing all message types
- `states/`: Folder containing all state modules
  - `client_state.py`: A globally accessible singleton containing client data including known peers, nicknames, recent messages, etc. 
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
- `--subnet`: Specifies the subnet mask, accepts the prefix of CIDR notation
- `--ipaddress`: Overrides the automatic IP address detection, useful for testing with VPNs


## Adding New Message Types
Each message is represented as a python file under the `messages/` folder. These are dynamically loaded by `router.py`. Each message type should be self validating, meaning that all instances of a message type should be considered valid. Instantiating new messages would also be automated and as such, each message type should:

- Inherit from `BaseMessage`, an abstract class defining what functionality the message should implement.
- Include `__schema__` under the implementing class, which dictates the format (the type of the message, including information such as the field data types) of the message.
- Include `__message__` inside the module, which points to the implementing class.
- As convention, match constructor variable ordering and name with its field names as defined in `__schema__` (typically lowercase versions of the keys).

In case the field name cannot be used as a constructor argument name, include an underscore on the end: e.g. from -> from_

Another subfolder can be used for dynamic allocation by changing `MESSAGES_DIR` in the `config.py` file.


### `__schema__`
Is a dictionary used by `validate_message` to validate the instance of the message type against. Each key value pair represents a field of the message. The first key value pair should always be `TYPE`: `MSG_TYPE` where msg_type is a hardcoded value.

- `KEY`: The name of the field (usually in ALL_CAPS)
- `VALUE`: The "rules" in dictionary form.

Each RULE may include the following flags:

- `type`: The allowed data type of the field's value
- `required`: If `True` the field's values cannot be empty

Example:
```
TYPE = "POST"
__schema__ = {
  "TYPE": cls.TYPE,
  "USER_ID": {"type": UserID, "required": True},
  "CONTENT": {"type": str, "required": True},
}
```
Where
- `TYPE`: Always the message type (e.g. "POST")
- `USER_ID`: Must be a UserID object
- `CONTENT`: Non-empty string
