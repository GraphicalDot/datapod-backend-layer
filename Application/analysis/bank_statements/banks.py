




BANKS = ["Allahabad Bank", "Andhra bank", "Bank of Baroda", "Bank of Maharashtra", 
    "Canara bank", "Central bank of india", "Corporation Bank", "Indian Bank", 
    "Indian Overseas bank", "Oriental bank of commerce", "punjab and sind bank", 
    "punjab national bank", "state bank of india", "syndicate bank", "uco bank", 
    "union bank of india", "United Bank of india", 
    "axis bank", "bandhan bak", "catholic syrian bank", "city union bank", "dcb bank",
    "dhanlaxmi bank", "federal bank", "hdfc bank", "icici bank", "idfc first bank", 
    "indusind bank", "jammu and kashmir bank", "karnatka bank", "karur vysya bank", 
    "kotak mahindra bank", "lakshmi vilas bank", "nainital bank", "rbl bank", 
    "south indian bank", "yes bank", "idbi bank", "tamilnad mercantile bank limited"
]


from collections import defaultdict


class TrieNode():

    def __init__(self):
        self.children = defaultdict()
        self.terminating = False


class Trie():

    def __init__(self):
        self.root = self.get_node()

    def get_node(self):
        return TrieNode()

    def get_index(self, ch):
        return ord(ch) - ord('a')

    def insert(self, word):

        root = self.root
        len1 = len(word)

        for i in range(len1):
            index = self.get_index(word[i])

            if index not in root.children:
                root.children[index] = self.get_node()
            root = root.children.get(index)

        root.terminating = True

    def search(self, word):
        root = self.root
        len1 = len(word)

        for i in range(len1):
            index = self.get_index(word[i])
            if not root:
                return False
            root = root.children.get(index)

        return True if root and root.terminating else False

    def delete(self, word):

        root = self.root
        len1 = len(word)

        for i in range(len1):
            index = self.get_index(word[i])

            if not root:
                print ("Word not found")
                return -1
            root = root.children.get(index)

        if not root:
            print ("Word not found")
            return -1
        else:
            root.terminating = False
            return 0

    def update(self, old_word, new_word):
        val = self.delete(old_word)
        if val == 0:
            self.insert(new_word)

    

if __name__ == "__main__":


    t = Trie()
    for bank in BANKS:
        t.insert(bank.lower())

    print (t.search("pqrs"))
    print (t.search("pprt"))

    #t.delete("pprt")

    #print t.search("pprt")

    #t.update("mnop", "pprt")