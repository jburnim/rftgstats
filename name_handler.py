import collections

class NameHandlerImpl:
    def __init__(self):
        self.cannonical_name = {}
        self.aliases = collections.defaultdict(list)
        self.collided_names = set()

        for line in open('name_collisions.txt', 'r'):
            self.collided_names.add(line.strip())

        for line in open('aliases.txt', 'r'):
            split_line = line.strip().split(',')
            primary = split_line[0]
            
            for source in split_line:
                self.cannonical_name[source] = primary
                if source != primary:
                    self.aliases[primary].append(source)

    def GetPrimaryName(self, name, server):
        #if name in self.collided_names:
        #    name = name + '@' + server
        if name in self.cannonical_name:
            return self.cannonical_name[name]
            
        return name

    def GetAliases(self, name):
        return self.aliases[name]
    
name_handler = NameHandlerImpl()

