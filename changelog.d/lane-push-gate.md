## Claude lane pushes

Update the adopter-owned Claude lane profile from the shipped profile. Remove its
`Bash(git push -u origin:*)` allow rule and install the Bash `PreToolUse` hook
with the updated launcher. Run `git push -u origin <branch>` as a standalone call
from the issued lane root.
