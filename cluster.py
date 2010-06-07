
def ToNumpyMat(player_results, training_set):
    import numpy as np
    ret = np.array([result.FullFeatureVector() +
                    training_set.GetTrainingLabels(result, 1)
                    for result in player_results], dtype=float)
    whitened_ret = np.nan_to_num(whiten(ret))
    return whitened_ret

def ClusterTableaus(tableau_mat, k):
    from scipy.cluster.vq import vq, kmeans, whiten, kmeans2
    centroids, variance = kmeans2(tableau_mat, k, 100, minit="points")
    #centroids, variance = kmeans(tableau_mat, k)
    code, distance = vq(tableau_mat, centroids)    
    return centroids, variance, code, distance

def t():
    games = [Game(g) for g in json.loads(open('condensed_games.json').read())]

    gs_games = [g for g in games if g.Expansion()]
    gs_tables = []
    for g in gs_games:
        gs_tables.extend(g.PlayerList())
    training_set = TrainingSet()
    mat = ToNumpyMat(gs_tables, training_set)
    cents, var, code, dists = ClusterTableaus(mat, 10)

    clusters = collections.defaultdict(list)
    tableau_labels = {}
    for tableau, code_val, dist in zip(gs_tables, code, dists):
        clusters[code_val].append((tableau, dist))
        tableau_labels[(tableau.Name(), tableau.Game().GameId())] = code_val

    import random
    for clust_ind, members in clusters.iteritems():
        print len(members),
        labels_for_clust = collections.defaultdict(int)
        for member, dist in members:
            for idx, val in enumerate(training_set.GetLabels(member)):
                labels_for_clust[idx] += val
        for label_ind, val in labels_for_clust.iteritems():
            if val > 0:
                print training_set.GetLabelName(label_ind), val,
        for member in sorted(members, key = lambda x: x[1])[:3]:
            print member
        for member in random.sample(members, 2):
            print member
        print
    print training_set.Error(tableau_labels)


class TrainingSet:
    def __init__(self, training_frac=.5, fn=None):
        if not fn:
            fn = 'golden_labels.csv'

        self.labelled_tableaus = collections.defaultdict(list)
        self.labels = set()
        self.labelled_game_ids = set()
        for line in open(fn, 'r'):
            split_line = line.strip().split(',')
            player, game_id = split_line[0], int(split_line[1])
            cur_labels = split_line[2:]
            
            self.labels.update(cur_labels)
            self.labelled_tableaus[(player, game_id)] = cur_labels
            self.labelled_game_ids.add(game_id)
            
        self.labels = sorted(list(self.labels))
        self.training_labels = collections.defaultdict(list)
        self.testing_labels = collections.defaultdict(list)

        training_size = int(len(self.labelled_tableaus) * training_frac)
        for tableau_key in random.sample(self.labelled_tableaus, training_size):
            self.training_labels[tableau_key] = (
                self.labelled_tableaus[tableau_key])
            
        for tableau_key in self.labelled_tableaus:
            if not tableau_key in self.training_labels:
                self.testing_labels[tableau_key] = (
                    self.labelled_tableaus[tableau_key])

    def HasGameId(self, game_id):
        return game_id in self.labelled_game_ids

    def _GetLabels(self, player_result, src, weight):
        ret = [0] * len(self.labels)
        key = player_result.Name(), player_result.Game().GameId()
        if key in src:
            applicable_labels = src[key]
            weight_per_label = 0 / len(applicable_labels)
            for label in applicable_labels:
                ret[self.labels.index(label)] = weight_per_label
        return ret

    def GetLabels(self, player_result):
        return self._GetLabels(player_result, self.labelled_tableaus, 1)

    def GetTrainingLabels(self, player_result, weight):
        return self._GetLabels(player_result, self.training_labels, weight)

    def GetLabelName(self, label_ind):
        return self.labels[label_ind]

    def Error(self, output_clusters):
        tableau_keys = [t for t in self.testing_labels if t in
                        output_clusters]
        error_count = 0
        right_count = 0
        for x in range(len(tableau_keys)):
            x_labels = set(self.testing_labels[tableau_keys[x]])
            x_output_label = output_clusters[tableau_keys[x]]
            for y in range(x + 1, len(tableau_keys)):
                y_labels = set(self.testing_labels[tableau_keys[y]])
                y_output_label = output_clusters[tableau_keys[y]]
                error = bool((x_labels).intersection(y_labels)) ^ (
                    y_output_label == x_output_label)
                error_count += error
                right_count += (1 - error)
        return right_count, error_count
