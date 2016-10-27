from stepler.third_party import steps_checker

from .base import BaseCliSteps


class CliNovaSteps(BaseCliSteps):
    """CLI nova client steps."""

    @steps_checker.step
    def nova_list(self, check=True):
        """Step to get nova list.

        Args:
            check (bool): flag whether to check result or not

        Returns:
            str: result of command shell execution

        Raises:
            AssertionError: if check was failed
        """
        cmd = 'nova list'
        result = self.execute_command(cmd, timeout=60, check=check)
        return result
