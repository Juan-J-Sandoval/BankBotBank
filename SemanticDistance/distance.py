def semanticDistance(request, response):
        wordsInCommon = []
        wordsInCommonVector = []
        index = 0
        for word1 in request:
            for word2 in response:
                #if word1[0] in word2[0] or word2[0] in word1[0] and word1[0] not in wordsInCommon:
                if word1[0] == word2[0] and word1[0] not in wordsInCommon:
                    wordsInCommon.append(word1)
                    wordsInCommonVector.append([word1[0], word1[1] + word2[1]])


        print(wordsInCommonVector)

        scale = 0
        for word in wordsInCommonVector:
            scale = scale + word[1]
        scale = (scale * 1)

        W = len(wordsInCommon)
        X = len(request)
        Y = len(response)
        
        distance = 1 - ((1 * W + scale)/(X + Y + scale))

        return distance

#find the shortest string that isnt a single letter or two so that slightly different lexemes are put together
#def shortestCommonString():
