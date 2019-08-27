package routes

import (
	"fmt"
	"github.com/gin-gonic/gin"
  	"net/http"
	"github.com/f26401004/ATG-io-platform-backend/models/userModel"
  	// "encoding/json"
  	// "io/ioutil"
)

type RegisterInfo struct {
	Username string
	AuthCode string
}

func RegisterEndpoint (c *gin.Context) {
	// decode the string into RegisterInfo struct
	var info RegisterInfo
	// check the data format
	if errCheck := c.ShouldBind(&info); errCheck != nil {
		fmt.Println(errCheck)
		c.String(http.StatusConflict, errCheck.Error());
		return
	}

	// insert the user into the database
	status, errInsert := userModel.InsertUser(info.Username, info.AuthCode)
	// if the username exist, then return the error message
	if (!status || errInsert != nil) {
		c.String(http.StatusConflict, errInsert.Error());
		return
	}

	c.String(http.StatusOK, "Register result: pass");
}
