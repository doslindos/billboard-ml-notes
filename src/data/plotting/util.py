from matplotlib import pyplot as plt

def makeHistogram(labels, data):
    plt.bar(labels, data)
    plt.xticks(range(1, len(labels)))
    plt.show()
