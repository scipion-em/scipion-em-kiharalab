def assertHandle(func, *args, cwd='', message=''):
  """
  ### This function runs the given assertion and handles the potential error, showing the protocol's error trace instead of a generic assertion.
  ### Note: Only designed to handle the assertions used by protocols.

  #### Params:
  - func (function): A function (assertion) to be executed.
  - *args: All the arguments passed to the function.
  - cwd (str): Optional. Current working directory. Usually protocol's cwd.
  - message (str): Optional. Custom message to display if no error messages were found in stdout/stderr.

  #### Example:
  assertHandle(self.assertIsNotNone, getattr(protocol, 'outputSet', None), cwd=protocol.getWorkingDir())
  """
  # Defining full path to error log
  stderr = os.path.abspath(os.path.join(cwd, 'logs', 'run.stderr'))
  stdout = os.path.abspath(os.path.join(cwd, 'logs', 'run.stdout'))

  # Attempt to run assertion
  try:
    return func(*args)
  except AssertionError:
    # If assertion fails, show error log
    # Getting error logs (stderr has priority over stdout)
    # Most errors are dumped on stderr, while some others on stdout
    errorMessage = ''
    for stdFile in [stderr, stdout]:
      if os.path.exists(stdFile):
        errorMessage = subprocess.run(['cat', stdFile], check=True, capture_output=True).stdout.decode()
        # Sometimes stderr file exists but it is empty, in those cases, fall back to stdout
        if errorMessage:
          break
    if not errorMessage:
      errorMessage = "Something went wrong with the protocol, but there are no stderr/stdout files right now, try manually opening the project to check it."
      if message:
        errorMessage += f"\n{message}"
    raise AssertionError(f"Assertion {func.__name__} failed for the following reasons:\n\n{errorMessage}")
    