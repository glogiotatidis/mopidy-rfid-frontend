from __future__ import unicode_literals

import logging
import pykka
import yaml
import gobject
import subprocess
import urllib

import beets
import mfrc522
import wiringpi2

logger = logging.getLogger(__name__)

MIFAREReader = mfrc522.MFRC522(dev='/dev/spidev0.0')
CHANNEL_IN = 13 # BCM GPIO
CHANNEL_OUT = 6 # BCM GPIO


class RFIDFrontend(pykka.ThreadingActor):

    def __init__(self, config, core):
        super(RFIDFrontend, self).__init__()
        self.core = core
        cardlist_filename = config['rfid-frontend']['cardlist']
        with open(cardlist_filename) as cardlistfp:
            self.cardlist = yaml.load(cardlistfp)
        self._setup_ports()
        self.beets_library = beets.Library(config['rfid-frontend']['beetslibrary'])
        self.card = None
        self.check_card()
        logger.info('RFID Frontend started')

    def _setup_ports(self):
        wiringpi2.wiringPiSetupSys()
        wiringpi2.pinMode(CHANNEL_OUT, 1)
        wiringpi2.digitalWrite(CHANNEL_OUT, 1)
        wiringpi2.pinMode(CHANNEL_IN, 0)
        # Pull down
        wiringpi2.pullUpDnControl(CHANNEL_IN, 1)

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
        pin_status = wiringpi2.digitalRead(CHANNEL_IN)
        logger.debug('Pin {}'.format(pin_status))
        if pin_status == 0:
            if not self.card:
                uid = self.read_rfid()
                if uid:
                    if uid in self.cardlist:
                        self.card = uid
                        self.card_added(uid)
                    else:
                        logger.info('Card added, no match.')
        else:
            if self.card:
                self.card = None
                self.card_removed()
        gobject.timeout_add(200, self.check_card)

    def card_added(self, uid):
        self.core.tracklist.clear()
        logger.info('Card added, cleared playlist')
        self.core.tracklist.set_single(False)
        logger.info('Card added, set single to False')
        uris = self.convert_uris(self.cardlist[uid])
        self.core.tracklist.add(uris=uris)
        logger.info('Card added, start playing')
        self.core.playback.play()

    def card_removed(self):
        self.core.playback.stop()
        logger.info('Card removed, stopped playback')
        self.core.tracklist.clear()
        logger.info('Card removed, cleared playlist')

    def convert_uris(self, uris):
        new_list = []
        for uri in uris:
            if uri.startswith('beetsquery:'):
                new_list.extend(self.beets_query(uri))
            else:
                new_list.append(uri)
        return new_list

    def beets_query(self, uri):
        query = uri.split(':', 1)[1]
        tracks = self.beets_library.items(query=query)
        return ['file://{}'.format(urllib.quote(track.path)) for track in tracks]
