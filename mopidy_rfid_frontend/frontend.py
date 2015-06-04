from __future__ import unicode_literals

import logging
import pykka
import yaml
import RPi.GPIO as GPIO
import MFRC522

logger = logging.getLogger(__name__)
MIFAREReader = MFRC522.MFRC522(dev='/dev/spidev0.0')
CHANNEL_IN = 33
CHANNEL_OUT = 31



class RFIDFrontend(pykka.ThreadingActor):

    def __init__(self, config, core):
        super(RFIDFrontend, self).__init__()
        cardlist_filename = config['rfid-frontend']['cardlist']
        # with open(cardlist_filename) as cardlistfp:
        #     cardlist = yaml.load(cardlistcp)

        self._setup_board()
        logger.info('RFID Frontend started')

    def _setup_rfid(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(CHANNEL_OUT, GPIO.OUT)
        GPIO.output([CHANNEL_OUT], GPIO.HIGH)
        GPIO.setup(CHANNEL_IN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(CHANNEL_IN, GPIO.BOTH, callback=self.check_card, bouncetime=500)

    def read_rfid(self):
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        if status != MIFAREReader.MI_OK:
            logger.info('Unabled to read card, first request')
            return
        (status,uid) = MIFAREReader.MFRC522_Anticoll()
        if status != MIFAREReader.MI_OK:
            logger.info('Unabled to read card, second request')
            return
        uid = ''.join(['%02x' % i for i in uid[:4]]).upper()
        return uid

    def check_card(self):
        if GPIO.input(CHANNEL_IN) == GPIO.LOW:
            uid = self.read_rfid()
            self.card_added(uid)
        else:
            self.card_removed()

    def card_added(self, uid):
        self.core.tracklist.clear()
        logger.info('Card added, cleared playlist')
        self.core.tracklist.set_single(False)
        logger.info('Card added, set single to False')
        self.core.tracklist.add(uris=uris)
        logger.info('Card added, start playing')
        self.core.playback.stop()

    def card_removed(self):
        self.core.playback.stop()
        logger.info('Card removed, stopped playback')
        self.core.tracklist.clear()
        logger.info('Card removed, cleared playlist')
