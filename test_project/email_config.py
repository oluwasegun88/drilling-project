from dataclasses import dataclass, field
from typing import List


@dataclass
class EmailConfig:
    smtp_host:  str       = "smtp.gmail.com"
    smtp_port:  int       = 587
    email:      str       = ""
    password:   str       = ""
    recipients: List[str] = field(default_factory=list)
    assets:     List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            email      = "olayemisegun.c@gmail.com",
            password   = "oxinozcaqsaleebj",
            recipients = ["nuclearstc@gmail.com", "gabriel.achumba@newcross.com"],
            assets     = ["OML 152", "OML 24", "OML 147"],
        )

    def validate(self):
        if not self.email:
            raise ValueError("Email is not set")
        if not self.password:
            raise ValueError("Password is not set")
        if not self.recipients:
            raise ValueError("Recipients is not set")