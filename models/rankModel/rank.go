package rankModel

import (
	"github.com/syndtr/goleveldb/leveldb"
	"encoding/json"
	"time"
)

var DBString string = "./models/DB/rank"


type RankData struct {
	ElapsedTime float32
	Status bool
	Score int
	UpdatedAt time.Time
}

type RankEntry struct {
	Username string
	ElapsedTime float32
	Status bool
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
		entry.Status = rankData.Status
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
		entry.Status = rankData.Status
		entry.Score = rankData.Score
		entry.Username = string(key)
		rankEntryList = append(rankEntryList, entry)
	}
	iter.Release()
	err := iter.Error()
	return rankEntryList, err
}

func UpsertRank (username string, elapsedTime float32, status bool, score int) (bool, error) {
	rankModel, DBError := leveldb.OpenFile(DBString, nil)
	defer rankModel.Close()
	if (DBError != nil) {
		return false, DBError
	}
	
	data := RankData {
		ElapsedTime: elapsedTime,
		Status: status,
		Score: score,
		UpdatedAt: time.Now(),
	}

	bytes, errMarshal := json.Marshal(data)
	if (errMarshal != nil) {
		return false, errMarshal
	}

	rankModel.Put([]byte(username), bytes, nil)
	return true, nil
}