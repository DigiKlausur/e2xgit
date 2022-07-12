import importlib
import os
from enum import Enum

from notebook.services.contents.filemanager import FileContentsManager
from tornado import web
from traitlets import Any, TraitError, validate


class FileOperations(Enum):
    RENAME = 1
    SAVE = 2
    DELETE = 3


class E2xFileContentsManager(FileContentsManager):

    post_file_op_hook = Any(
        None,
        config=True,
        allow_none=True,
        help="""Python callable or importstring thereof
        to be called on the path of a file just changed.
        This hook is called on renaming, removing, creating and saving files 
        """,
    )

    @validate("post_file_op_hook")
    def _validate_post_file_op_hook(self, proposal):
        value = proposal["value"]
        if isinstance(value, str):
            module, function = value.rsplit(".", 1)
            value = getattr(importlib.import_module(module), function)
        if not callable(value):
            raise TraitError("post_file_op_hook must be callable")
        return value

    def run_post_file_op_hook(self, action, options):
        """Run the post file op hook if defined, and log errors"""
        self.log.info(f"About to run hook with action={action}, options={options}")
        if self.post_file_op_hook:
            try:
                self.log.debug("Running post file op hook")
                self.log.info(
                    f"About to really run hook with action={action}, options={options}"
                )
                self.post_file_op_hook(action=action, options=options)
            except Exception as e:
                self.log.error("Post file op hook failed", exc_info=True)
                raise web.HTTPError(
                    500, f"Unexpected error while running post file op hook: {e}"
                ) from e

    def rename_file(self, old_path, new_path):
        self.log.info(f"Rename {old_path} -> {new_path}")
        res = super().rename_file(old_path, new_path)
        self.run_post_file_op_hook(
            action=FileOperations.RENAME,
            options=dict(
                old_path=os.path.join(self.root_dir, old_path.lstrip("/")),
                path=os.path.join(self.root_dir, new_path.lstrip("/")),
            ),
        )
        return res

    def delete_file(self, path):
        self.log.info(f"Delete {path}")
        res = super().delete_file(path)
        self.run_post_file_op_hook(
            action=FileOperations.DELETE,
            options=dict(path=os.path.join(self.root_dir, path.lstrip("/"))),
        )
        return res

    def save(self, model, path=""):
        self.log.info(f"Save {path}")
        res = super().save(model, path)
        self.run_post_file_op_hook(
            action=FileOperations.SAVE,
            options=dict(
                model=model, path=os.path.join(self.root_dir, path.lstrip("/"))
            ),
        )
        return res
