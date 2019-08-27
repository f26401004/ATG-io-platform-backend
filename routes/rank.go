package routes

import (
	"github.com/gin-gonic/gin"
	"net/http"
  "github.com/f26401004/ATG-io-platform-backend/models/rankModel"
  "github.com/f26401004/ATG-io-platform-backend/models/userModel"
	"golang.org/x/crypto/bcrypt"
)

type PostRankInfo struct {
  AuthCode string
  ElapsedTime float32
  Score int
  Status bool
}

func RankEndpoint (c *gin.Context) {
  username := c.Query("username")
  rankEntry, getRankError := rankModel.GetRank(username)
  if (getRankError != nil) {
    c.String(http.StatusBadRequest, getRankError.Error());
    return
  }
  c.JSON(http.StatusOK, rankEntry)
}

func UpsertRankEndpoint (c *gin.Context) {
  username := c.Param("username")
  // decode the string into RegisterInfo struct
  var info PostRankInfo
	// check the data format
	if errCheck := c.ShouldBind(&info); errCheck != nil {
		c.String(http.StatusConflict, errCheck.Error())
		return
  }

  // check authCode
  userData, errGetUser := userModel.GetUser(username)
  if (errGetUser != nil) {
		c.String(http.StatusConflict, errGetUser.Error())
    return
  }
  errCompare := bcrypt.CompareHashAndPassword([]byte(userData.AuthCode), []byte(info.AuthCode))
  if (errCompare != nil) {
    c.String(http.StatusConflict, "The authCode do not match.")
    return
  }

  rankModel.UpsertRank(username, info.ElapsedTime, info.Status, info.Score)

}