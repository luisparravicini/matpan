from setup import setup


_, _, _, _, all_data, ckp_manager, strategy = setup()

strategy.run()

print(strategy.returns)
