package routes

import (
	"github.com/gin-gonic/gin"
	"net/http"
    "github.com/gorilla/websocket" 
	"github.com/f26401004/ATG-io-platform-backend/models/userModel"
    "golang.org/x/crypto/bcrypt"
    "encoding/json"
    "github.com/f26401004/ATG-io-platform-backend/simulation"
)

type User struct {
    Username string
    AuthCode string
}

var upGrader = websocket.Upgrader{  
    CheckOrigin: func (r *http.Request) bool {  
        return true  
    },
}  

func SimulationEndpoint (c *gin.Context) {
    ws, errUpgrader := upGrader.Upgrade(c.Writer, c.Request, nil)  
    if errUpgrader != nil {  
        c.String(http.StatusBadRequest, errUpgrader.Error())
        return
    }

    // record the error in for loop
    for {
        // register current simulation with user information
        _, message, errRead := ws.ReadMessage()  
        if errRead != nil {
            break  
        }
        // check the first message met the format
        var target User
        errUnmarshal := json.Unmarshal(message, &target)
        if (errUnmarshal != nil) {
            
            break
        }
        // check the username and authCode
        userData, errGetUser := userModel.GetUser(target.Username)
        if (errGetUser != nil) {
            ws.Close()
            break
        }
        errCompare := bcrypt.CompareHashAndPassword([]byte(userData.AuthCode), []byte(target.AuthCode))
        if (errCompare != nil) {
            ws.Close()
            break
        }

        // send the simulation info to the worker
        simulation.StartSimulation(userData.Username, ws)
        break
    }
}
