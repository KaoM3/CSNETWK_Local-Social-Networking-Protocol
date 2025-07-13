# TODO: Implement Schema
dm_schema = {
  "TYPE": "DM",
  "FROM": {"type": str, "required": True},
  "TO": {"type": str, "required": True},
  "CONTENT": {"type": str, "required": True},
  "TIMESTAMP": {"type": str, "required": True},
  "MESSAGE_ID": {"type": str, "required": True},
  "TOKEN": {"type": str, "required": True},
}

# TODO: Implement send()
# TODO: Implement receive()