-- CreateIndex
CREATE INDEX "Event_eventTime_idx" ON "Event"("eventTime");

-- CreateIndex
CREATE INDEX "Event_artifactId_eventType_eventTime_idx" ON "Event"("artifactId", "eventType", "eventTime");
