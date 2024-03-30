# SMU-IV-Curve

Currently only GPIB::1 and IP connection are setup
TODO DeviceConnection:
	Find way to test if the device is actually connected
TODO GPIB:
	Add another window similar to IP connection to take in integer between 0-99

TODO USB:
	Implement it I haven't looked into this at all

TODO runSMU:
	Test SMU code make sure it actually works
	Setup run to use parameters
	Send data to runInformation screen for plotting
	Setup to pull device1 and device2 from dropdown selection
	Setup to prompt user for manual input if device2 == Power Supply
	1) Setup to run a standard sweep and measure outputs to make sure code is working
	2) Setup sweep to handle inputs from the UI
	3) Get everything else working

NoneTypeobject has no attribute reset -> Device failed to connect