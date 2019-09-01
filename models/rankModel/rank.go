package rankModel

import (
	"github.com/syndtr/goleveldb/leveldb"
	"encoding/json"
	"time"
)

var DBString string = "./models/DB/rank"


type RankData struct {
	ElapsedTime float32
	Result bool
	Score int
	UpdatedAt time.Time
}

type RankEntry struct {
	Username string
	ElapsedTime float32
	Result bool
	Score int
	UpdatedAt time.Time
}

func GetRank (username string) ([]RankEntry, error) {
	rankModel, DBError := leveldb.OpenFile(DBString, nil)
	defer rankModel.Close()
	if (DBError != nil) {
		return nil, DBError
	}
	if (len(username) > 0) {
		data, getError := rankModel.Get([]byte(username), nil)
		if (getError != nil) {
			return nil, getError
		}
		// initialize a memory space to encode the data into rank entry
		var rankData RankData
		json.Unmarshal(data, &rankData)
		// initialize a memory space to format the data
		var entry RankEntry
		entry.ElapsedTime = rankData.ElapsedTime
		entry.UpdatedAt = rankData.UpdatedAt
		entry.Result = rankData.Result
		entry.Score = rankData.Score
		entry.Username = username
		return []RankEntry{entry}, nil
	}
	var rankEntryList []RankEntry
	// get all rank data from database
	iter := rankModel.NewIterator(nil, nil)
	for iter.Next() {
		key := iter.Key()
		value := iter.Value()

		// initialize a memory space to encode the data into rank entry
		var rankData RankData
		json.Unmarshal(value, &rankData)

		// initialize a memory space to format the data
		var entry RankEntry
		entry.ElapsedTime = rankData.ElapsedTime
		entry.UpdatedAt = rankData.UpdatedAt
		entry.Result = rankData.Result
		entry.Score = rankData.Score
		entry.Username = string(key)
		rankEntryList = append(rankEntryList, entry)
	}
	iter.Release()
	err := iter.Error()
	return rankEntryList, err
}

func UpsertRank (username string, elapsedTime float32, result bool, score int) (bool, error) {
	rankModel, errDB := leveldb.OpenFile(DBString, nil)
	defer rankModel.Close()
	if (errDB != nil) {
		return false, errDB
	}
	// get teh data from database
	entryByte, errGet := rankModel.Get([]byte(username), nil)
	if (errGet != nil) {
		return false, errGet
	}
	var entry RankData
	errUnmarshal := json.Unmarshal(entryByte, &entry)
	if (errUnmarshal != nil) {
		return false, errUnmarshal
	}
	// compare the origin ranking data
	if (entry.Result != result) {
		entry.Result = result
		entry.ElapsedTime = elapsedTime
	}
	if (entry.ElapsedTime > elapsedTime && entry.Result == result) {
		entry.ElapsedTime = elapsedTime
	}
	if (entry.Score < score) {
		entry.Score = score
	}


	bytes, errMarshal := json.Marshal(entry)
	if (errMarshal != nil) {
		return false, errMarshal
	}

	rankModel.Put([]byte(username), bytes, nil)
	return true, nil
}