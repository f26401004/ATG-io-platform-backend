package userModel

import (
	"github.com/syndtr/goleveldb/leveldb"
	"golang.org/x/crypto/bcrypt"
	"errors"
	"fmt"
)

var DBString string = "./models/DB/user";

type User struct {
	Username string
	AuthCode string
}

func GetUser (username string) (User, error) {
	userModel, DBError := leveldb.OpenFile(DBString, nil)
	defer userModel.Close()
	if (DBError != nil) {
		return User{}, DBError
	}
	authCode, err := userModel.Get([]byte(username), nil)
	if (err != nil) {
		return User{}, err
	}
	if (len(authCode) == 0) {
		return User{}, errors.New("The account do not exist.")
	}
	var user User
	user.Username = username
	user.AuthCode = string(authCode)
	return user, nil
}

func InsertUser (username, authCode string) (bool, error) {
	userModel, errDB := leveldb.OpenFile(DBString, nil)
	defer userModel.Close()
	if (errDB != nil) {
		return false, errDB
	}
	data, _ := userModel.Get([]byte(username), nil)

	if (len(data) > 0) {
        errCompare := bcrypt.CompareHashAndPassword(data, []byte(authCode))
		if (errCompare != nil) {
			fmt.Println(errCompare)
			return false, errors.New("The username has been used already.")
		}
		return true, nil
	}
	
	hashed, _ := bcrypt.GenerateFromPassword([]byte(authCode), bcrypt.MinCost)
	userModel.Put([]byte(username), hashed, nil)
	return true, nil
}