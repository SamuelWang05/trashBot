# trashBot
This is a Discord trash bot to keep track of roommate agreement

<img src="https://github.com/SamuelWang05/trashBot/blob/main/trashBot_img.jpg" width="300" />

Despite our best attemps, a whiteboard to keep track of who should take out the trash was not successful. Thus, the trashBot was born.

The trashBot utilizes the Discord API to ping one user (out of the 10 roommates) every Sunday at 8am. If they do not take out the trash by next week Sunday 8am, they accumulate "debt". Debt means that they have to take out trash for the next week as well!

# List of currently available commands

- **!start** - Start the weekly pinger.
- **!stop** - Stop the weekly pinger.
- **!complete** - Mark your task as complete.
- **!who** - See who's turn it is to take out the trash.
- **!debt** - List all users' debt.
- **!commands** - List all available commands.

# Potential Future Functionality
- !sweep: By completing a sweeping on the first/second floor, you can reduce your debt by 1 per floor
- !remind: Set a reminder for yourself to take out the trash. Customize the time to remind yourself
- !leaderboard: Point system for taking out the trash. Points awarded for least debt, etc.
- !steal: Take out the trash before the designated person for the week to climb up the leaderboards
