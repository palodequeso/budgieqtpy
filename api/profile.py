class ProfileAPI:
    def __init__(self, db):
        self.db = db

    def get_profiles(self):
        return self.db.fetch_profiles()

    def get_profile_by_id(self, profile_id):
        profiles = self.db.fetch_profiles()
        profile = next((p for p in profiles if p.id == profile_id), None)
        if profile is None:
            raise ValueError(f"Profile with id {profile_id} not found")
        profile.accounts = self.db.fetch_accounts(profile_id)
        # Fetch ledger entries for each account
        for account in profile.accounts:
            account.ledger = self.db.fetch_ledger_items(account.id)
        profile.budget_groups = self.db.fetch_budget_groups(profile_id)
        profile.budget_items = self.db.fetch_budget_items(profile_id)
        return profile

    def create_profile(self, name):
        return self.db.create_profile(name)
