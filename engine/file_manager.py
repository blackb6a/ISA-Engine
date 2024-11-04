from engine.error import ISAError, ISAErrorCodes


class FileManager:
    def __init__(
        self,
        vfiles: dict[bytes, bytes] = {},
    ):
        self.vfiles = {}
        for name, content in vfiles.items():
            if isinstance(name, bytes):
                vfile_name = name
            elif isinstance(name, str):
                vfile_name = name.encode()
            else:
                raise ISAError(ISAErrorCodes.BAD_CONFIG, "invalid vfile name")

            if isinstance(content, bytes):
                vfile_content = content
            elif isinstance(content, str):
                vfile_content = content.encode()
            else:
                raise ISAError(ISAErrorCodes.BAD_CONFIG, "invalid vfile content")

            self.insert({vfile_name: vfile_content})

    def __getitem__(self, filename: bytes) -> dict | None:
        if filename not in self.vfiles.keys():
            return None
        file = self.vfiles[filename]
        return {
            "size": len(file),
            "content": file,
        }

    def insert(self, vfiles: dict[bytes, bytes]):
        self.vfiles.update(vfiles)

    def prune(self):
        self.vfiles.clear()

    def list(self):
        return list(self.vfiles.keys())
