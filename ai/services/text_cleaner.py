import re


class TextCleaner:

    @staticmethod
    def clean(text: str) -> str:

        if not text:
            return ""

        text = text.replace("\r\n", "\n")

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        return text.strip()