from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        self._escursioni_parco=[] #Lista delle escursioni appartenenti al parco selezionato
        self._max_giorni=None #Vincolo sulla durata massima in giorni
        self._max_budget=None #Vincolo sul costo massimo del pacchetto
        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # TODO
        #Recupero dal DAO le coppie
        relazioni=EscursioneDAO.get_escursioni_punti_interesse()

        for rel in relazioni:
            #Recupero i rispettivi oggetti (Escursione e PuntoInteresse)
            escursione=self.escursioni_map.get(rel["id_escursione"])
            punto_interesse=self.punti_interesse_map.get(rel["id_punto_interesse"])

            # Verifico che entrambi gli oggetti esistano e crea il collegamento bidirezionale
            if escursione is not None and punto_interesse is not None:
                escursione.punti_interesse.add(punto_interesse) #Aggiungo il punto di interesse al set dell'escursione
                punto_interesse.escursioni.add(escursione) #Aggiungo l'escursione al set del punto di interesse


    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # TODO
        #Salvo negli attributi del Model i vincoli scelti dall'utente
        self._max_budget = max_budget
        self._max_giorni = max_giorni
        self._escursioni_parco=[]

        #Filtro solo le escursioni che appartengono al parco selezionato
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                self._escursioni_parco.append(escursione)

        #Avvio la ricorsione partendo dall'indice 0
        self._ricorsione(0, [],0,0,0,set())
        #Restituisco al controller la lista migliore trovata, il suo costo totale e il voto complessivo
        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
        # 1. Valuto il pacchetto attuale
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()

        #Esploro le escursioni rimanenti a partire da start_index
        for i in range(start_index, len(self._escursioni_parco)):
            esc = self._escursioni_parco[i]
            #Verifico se aggiungere questa escursione rispetta durata, budget e unicità dei punti di interesse
            if self._vincoli_soddisfatti(esc, durata_corrente, costo_corrente, punti_usati):
                valore_esc = self._calcola_valore(esc)
                #Creo una nuova lista e aggiorno tutti i contatori
                self._ricorsione(
                    i + 1,
                    pacchetto_parziale + [esc],
                    durata_corrente + esc.durata_giorni,
                    costo_corrente + esc.costo,
                    valore_corrente + valore_esc,
                    punti_usati | esc.punti_interesse
                )

    def _vincoli_soddisfatti(self, nuova_esc, durata_corrente, costo_corrente, punti_usati):
        #Controllo durata massima in giorni
        if self._max_giorni is not None and durata_corrente + nuova_esc.durata_giorni > self._max_giorni:
            return False

        #Controllo budget
        if self._max_budget is not None and costo_corrente + nuova_esc.costo > self._max_budget:
            return False

        #Controllo punti di interesse unici
        if not punti_usati.isdisjoint(nuova_esc.punti_interesse):
            return False

        return True

    def _calcola_valore(self, esc):
        #Inizializzo l'accumulatore del punteggio a zero
        totale = 0
        #Scorro tutti gli oggetti PuntoInteresse associati all'escursione corrente
        for punto in esc.punti_interesse:
            totale += punto.voto_visitatori
        #Restituisco il punteggio totale ottenuto dall'escursione
        return totale

