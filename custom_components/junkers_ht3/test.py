from .driver import Ht3Driver
import time


def message(name, value):
    print("{} - {}".format(name, value))


driver = Ht3Driver("raspberrypi-cv")
driver.set_callback(message)
driver.start()
# driver.connect()

# driver.crc_get("AED1AEAE")

# driver.run()
# driver.writeHC_mode(2)
driver.writeHC_Trequested(21.5)

time.sleep(60)

driver.stop()

# while True:
# driver.read()
#    i=0
