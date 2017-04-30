# RocketMap tutorial completion for accounts (up to Level 2)
This is a guide on how to complete the Pokémon Go tutorial steps and becoming
level 2 on your accounts as fast as possible, so you can use `-tut` once
on all accounts and disable it again afterwards.

## Instruction
* We assume you are running a basic RocketMap installation. Using the hashing
service with the latest API version will avoid accounts being flagged.
* Create a ``config/config.tutorial.ini`` file by copying and renaming
``config/config.ini.example`` and make the following changes:
* Config changes are:
	* Set location next to at least one known Pokestop, a cluster is preferred.
	* Set step distance to ``st: 1``.
	* Set scan delay ``sd`` to a value which provides enough calls during the
	following set search time (a good value is around ``sd: 15`` or lower).
	* Set the account search interval to approx. ``asi: 120``.
	* Set the account rest interval as high as possible so all accounts get
	cycled and none return, a safe value is ``ari: 36000``.
	* Set login delay to at least ``login-delay: 1`` to avoid throttling.
* Put the accounts that need to complete the tutorial and need to level up 
into your ``accounts.csv`` file.
* Set up an instance with the following flags:
	* ``--complete-tutorial`` or just ``-tut``
	* ``--config config/config.tutorial.ini`` or just
	``-cf config/config.tutorial.ini`` to use a designated config file.
	* ``--accountcsv PATH/accounts.csv`` or just ``-ac PATH/accounts.csv``
	* ``-w WORKER`` to set your simultaneously working accounts to a reasonable
	number, considering hash key limit and throttling. You can have at least 10
	accounts running at the same time without any problems.
* If you are not using fresh accounts and you are not using the hashing service,
prepare for captchas. Set up your RocketMap accordingly.
* Enable ``-v`` in process if you want to see the debug logs.
* Let it run and your accounts will complete the tutorial and rise to level 2.
