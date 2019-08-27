package main

import (
    "github.com/gin-gonic/gin"
    // "net/http"
    "github.com/f26401004/ATG-io-platform-backend/routes"
    "github.com/f26401004/ATG-io-platform-backend/simulation"
    "github.com/gin-contrib/cors"
)

func main() {
    // initialize the server router
    router := gin.Default()
    router.Use(cors.Default())
    // server serve frontend static files.
    router.StaticFile("/", "./public")

    // initialize the simulation environment
    simulation.InitSimulationEnvironment()

    api := router.Group("/api")
    {
        api.GET("/rank", routes.RankEndpoint)
        api.GET("/compile", routes.CompileEndpoint)
        api.GET("/simulation", routes.SimulationEndpoint)
        api.POST("/register", routes.RegisterEndpoint)
        api.POST("/rank/:username", routes.UpsertRankEndpoint)
        api.POST("/upload", routes.UploadEndpoint)
    }
    router.Run("localhost:3000")
}

