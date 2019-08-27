package routes

import (
	"github.com/gin-gonic/gin"
  // "net/http"
  "fmt"
)

func UploadEndpoint (c *gin.Context) {
  // use form format to get the data
  file, _ := c.FormFile("file")
  username := c.PostForm("username")
  c.SaveUploadedFile(file, fmt.Sprintf("./codes/%s.cpp", username))
}