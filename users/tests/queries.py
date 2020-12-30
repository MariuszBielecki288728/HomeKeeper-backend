REGISTER_MUTATION = """mutation {{
  register (input: {{
    username: \"{username}\"
    password1: \"{password}\"
    password2: \"{password}\"
    email: \"{email}\"
  }}) {{
    username
    errors {{
      field
      messages
    }}
  }}
}}"""
