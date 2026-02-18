class AgentState:
    """
    Stores session memory for the agent.
    """

    def __init__(self):
        self.active_workbook = None

    def set_active_workbook(self, filepath: str):
        self.active_workbook = filepath

    def get_active_workbook(self):
        return self.active_workbook

