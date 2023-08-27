'''
rankings.db database schema:
CREATE TABLE IF NOT EXISTS "DataSets" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_DataSets" PRIMARY KEY AUTOINCREMENT,
    "CollectedAt" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "Episodes" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Episodes" PRIMARY KEY AUTOINCREMENT,
    "DurationMs" INTEGER NOT NULL,
    "Explicit" INTEGER NOT NULL,
    "Href" TEXT NOT NULL,
    "SpotifyId" TEXT NOT NULL,
    "IsExternallyHosted" INTEGER NOT NULL,
    "IsPlayable" INTEGER NOT NULL,
    "Language" TEXT NOT NULL,
    "ReleaseDate" TEXT NOT NULL,
    "ReleaseDatePrecision" TEXT NOT NULL,
    "Type" TEXT NOT NULL,
    "SpotifyUri" TEXT NOT NULL,
    "Description" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "PodcastId" INTEGER NOT NULL,
    CONSTRAINT "FK_Episodes_Podcasts_PodcastId" FOREIGN KEY ("PodcastId") REFERENCES "Podcasts" ("Id") ON DELETE CASCADE
);
CREATE INDEX "IX_Episodes_PodcastId" ON "Episodes" ("PodcastId");
CREATE TABLE IF NOT EXISTS "Podcasts" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Podcasts" PRIMARY KEY AUTOINCREMENT,
    "ShowUri" TEXT NOT NULL,
    "ChartRankMove" TEXT NOT NULL,
    "ShowImageUrl" TEXT NOT NULL,
    "ShowName" TEXT NOT NULL,
    "ShowPublisher" TEXT NOT NULL,
    "ShowDescription" TEXT NOT NULL,
    "Genre" TEXT NOT NULL,
    "IsExplicit" INTEGER NOT NULL,
    "Market" TEXT NOT NULL
);
CREATE UNIQUE INDEX "IX_Podcasts_ShowUri" ON "Podcasts" ("ShowUri");
CREATE TABLE IF NOT EXISTS "RankedPodcasts" (
    "RankingId" INTEGER NOT NULL,
    "PodcastId" INTEGER NOT NULL,
    "Rank" INTEGER NOT NULL,
    CONSTRAINT "PK_RankedPodcasts" PRIMARY KEY ("RankingId"  "PodcastId"),
    CONSTRAINT "FK_RankedPodcasts_Podcasts_PodcastId" FOREIGN KEY ("PodcastId") REFERENCES "Podcasts" ("Id") ON DELETE CASCADE,
    CONSTRAINT "FK_RankedPodcasts_Rankings_RankingId" FOREIGN KEY ("RankingId") REFERENCES "Rankings" ("Id") ON DELETE CASCADE
);
CREATE INDEX "IX_RankedPodcasts_PodcastId" ON "RankedPodcasts" ("PodcastId");
CREATE TABLE IF NOT EXISTS "Rankings" (
    "Id" INTEGER NOT NULL CONSTRAINT "PK_Rankings" PRIMARY KEY AUTOINCREMENT,
    "Genre" TEXT NOT NULL,
    "Country" TEXT NOT NULL,
    "PodcastDataSetId" INTEGER NULL,
    CONSTRAINT "FK_Rankings_DataSets_PodcastDataSetId" FOREIGN KEY ("PodcastDataSetId") REFERENCES "DataSets" ("Id")
);
CREATE INDEX "IX_Rankings_PodcastDataSetId" ON "Rankings" ("PodcastDataSetId");
'''